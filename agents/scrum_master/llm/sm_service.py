from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import asyncio
from openai import AsyncOpenAI
from backend.config import Config
from agents.core.monitoring.decorators import monitor_llm, monitor_operation
from agents.scrum_master.llm.sm_prompts import (
    format_user_request_analysis_prompt,
    format_requirement_clarification_prompt,
    format_technical_translation_prompt,
    format_feedback_analysis_prompt,
    format_milestone_presentation_prompt,
    format_status_report_prompt,
    format_question_answering_prompt
)
from core.logging.logger import setup_logger
from core.tracing.service import trace_class

@trace_class
class ScrumMasterLLMService:
    """
    LLM service specialized for Scrum Master Agent operations.
    Focuses on user communication, technical translation, and feedback processing.
    """
    
    def __init__(self, model: str = "gpt-4"):
        """
        Initialize the LLM service with configuration and API setup.
        
        Args:
            model (str): The OpenAI model to use. Defaults to "gpt-4".
        
        Raises:
            ValueError: If API key is missing or invalid
            Exception: For other initialization failures
        """
        self.logger = setup_logger("llm.scrum_master.service")
        self.logger.info("Initializing Scrum Master LLM Service")
        self.model = model
        
        try:
            self._initialize_client()
        except Exception as e:
            self.logger.error(f"Failed to initialize Scrum Master LLM Service: {str(e)}", exc_info=True)
            raise

    def _initialize_client(self) -> None:
        """Initialize the OpenAI client with proper configuration."""
        config_instance = Config()
        self.api_key = config_instance.OPENAI_API_KEY
        
        if not self.api_key:
            self.logger.error("OpenAI API key not found in configuration")
            raise ValueError("OpenAI API key not found in environment variables")
        
        # Log the first few characters of the API key to verify it's loaded (safely)
        key_preview = self.api_key[:4] + '*' * (len(self.api_key) - 8) + self.api_key[-4:]
        self.logger.debug(f"Loaded API key: {key_preview}")
            
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.logger.info(f"Scrum Master LLM Service initialized with model: {self.model}")
    
    async def _validate_api_key(self) -> None:
        """
        Validate the API key by making a test request.
        
        Raises:
            ValueError: If the API key is invalid
        """
        try:
            await self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use cheaper model for validation
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            self.logger.info("API key validation successful")
        except Exception as e:
            self.logger.error(f"API key validation failed: {str(e)}")
            raise ValueError(f"Invalid OpenAI API key: {str(e)}")

    async def _create_chat_completion(
        self,
        messages: list,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        """
        Create a chat completion with error handling and logging.
        
        Args:
            messages (list): List of message dictionaries
            temperature (float): Model temperature
            max_tokens (int): Maximum tokens in response
            
        Returns:
            str: Model response content
            
        Raises:
            Exception: If API call fails
        """
        try:
            self.logger.debug(f"Calling OpenAI API with model: {self.model}")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error in chat completion: {str(e)}", exc_info=True)
            raise

    @monitor_operation(
        operation_type="llm_response_parsing",
        include_in_parent=True
    )
    async def _parse_llm_response(self, response: str, expected_keys: Optional[list] = None) -> Dict[str, Any]:
        """
        Parse and validate the LLM response into a structured format.
        
        Args:
            response (str): The raw response string from the LLM
            expected_keys (Optional[list]): List of keys expected in the response
        
        Returns:
            Dict[str, Any]: Parsed and validated response
            
        Raises:
            json.JSONDecodeError: If response is not valid JSON
            ValueError: If response is missing expected keys
        """
        self.logger.debug("Parsing LLM response")
        try:
            # Extract JSON content from the response if needed
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                # Extract JSON part
                json_content = response[json_start:json_end]
                parsed_response = json.loads(json_content)
            else:
                # Try parsing the whole response
                parsed_response = json.loads(response)
            
            if expected_keys:
                missing_keys = [key for key in expected_keys if key not in parsed_response]
                if missing_keys:
                    self.logger.warning(f"Response missing expected keys: {missing_keys}")
                    
                    # Try to salvage what we can and fill in missing keys with defaults
                    for key in missing_keys:
                        if isinstance(key, str):
                            if "feedback" in key or "suggestions" in key:
                                parsed_response[key] = []
                            elif "analysis" in key or "result" in key or "details" in key:
                                parsed_response[key] = {}
                            else:
                                parsed_response[key] = ""
            
            self.logger.debug("Successfully parsed LLM response")
            return parsed_response
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response: {str(e)}", exc_info=True)
            # Try to create a structured response from unstructured text
            if response:
                return {"text": response, "parsing_error": str(e)}
            raise
        except Exception as e:
            self.logger.error(f"Error processing LLM response: {str(e)}", exc_info=True)
            raise

    #--------------------------------------------------------------------------
    # User Request Analysis Methods
    #--------------------------------------------------------------------------
    
    @monitor_llm(
        run_name="analyze_user_request",
        metadata={
            "operation_details": {
                "prompt_template": "user_request_analysis",
                "max_tokens": 1500,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def analyze_user_request(
        self,
        user_input: str,
        user_history: Optional[List[Dict[str, Any]]] = None,
        project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a user request to determine intent, type, and required actions.
        
        Args:
            user_input: Raw input from the user
            user_history: Optional history of user interactions
            project_context: Optional context about current projects
            
        Returns:
            Dict[str, Any]: Analysis of the user request
            
        Raises:
            Exception: If analysis fails
        """
        self.logger.info("Analyzing user request")
        
        try:
            # Format prompt for user request analysis
            formatted_prompt = format_user_request_analysis_prompt(
                user_input=user_input,
                user_history=user_history,
                project_context=project_context
            )

            # Call LLM for user request analysis
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Scrum Master AI with expertise in understanding user requests and requirements."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=1500
            )

            # Parse and validate response
            expected_keys = ["request_type", "intent", "requires_technical_knowledge", "requires_pm_input", "next_steps"]
            analysis_result = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info(f"Analyzed user request as type: {analysis_result.get('request_type', 'unknown')}")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Error analyzing user request: {str(e)}", exc_info=True)
            # Return basic analysis if it fails
            return {
                "request_type": "unknown",
                "intent": "Could not determine intent due to error",
                "requires_technical_knowledge": False,
                "requires_pm_input": False,
                "requires_team_lead_input": False,
                "priority": "MEDIUM",
                "next_steps": ["Ask user to clarify their request"],
                "clarification_needed": True,
                "clarification_questions": ["Could you please clarify what you're looking for?"],
                "error": str(e)
            }

    #--------------------------------------------------------------------------
    # User Preference and Communication Style Methods
    #--------------------------------------------------------------------------
    
    @monitor_llm(
        run_name="analyze_user_preferences",
        metadata={
            "operation_details": {
                "prompt_template": "user_preference_analysis",
                "max_tokens": 1000,
                "temperature": 0.2,
                "response_format": "structured_json"
            }
        }
    )
    async def analyze_user_preferences(
        self,
        user_interactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze user interactions to infer communication preferences.
        
        Args:
            user_interactions: History of user interactions
            
        Returns:
            Dict[str, Any]: Inferred user preferences
            
        Raises:
            Exception: If preference analysis fails
        """
        self.logger.info("Analyzing user preferences from interaction history")
        
        try:
            if not user_interactions:
                return {
                    "technical_level": "beginner",
                    "communication_style": "friendly",
                    "detail_preference": "medium",
                    "visualization_preference": "medium",
                    "confidence": 0.5,
                    "insufficient_data": True
                }
            
            # Format user interactions for the prompt
            interactions_text = ""
            for i, interaction in enumerate(user_interactions[-5:]):  # Use last 5 interactions
                user_message = interaction.get("user_message", "")
                interactions_text += f"Interaction {i+1}:\n{user_message}\n\n"
            
            # Create prompt for preference analysis
            prompt = f"""
            As a Scrum Master AI, analyze the following user interactions to infer their communication preferences:

            USER INTERACTIONS:
            {interactions_text}

            Based on these interactions, infer the user's preferences for:
            1. Technical level (beginner, intermediate, advanced)
            2. Communication style (formal, friendly, direct)
            3. Detail preference (minimal, medium, detailed)
            4. Visualization preference (minimal, medium, detailed)

            Format your response as a JSON object with:
            {{
                "technical_level": "beginner/intermediate/advanced",
                "communication_style": "formal/friendly/direct",
                "detail_preference": "minimal/medium/detailed",
                "visualization_preference": "minimal/medium/detailed",
                "confidence": 0.0-1.0,
                "reasoning": "Brief explanation of your analysis"
            }}
            """

            # Call LLM for preference analysis
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Scrum Master AI with expertise in analyzing communication patterns and preferences."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.2  # Low temperature for consistent analysis
            )

            # Parse and validate response
            expected_keys = ["technical_level", "communication_style", "detail_preference"]
            preferences = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info(f"Inferred user preferences: technical level = {preferences.get('technical_level', 'unknown')}")
            return preferences
            
        except Exception as e:
            self.logger.error(f"Error analyzing user preferences: {str(e)}", exc_info=True)
            # Return default preferences if it fails
            return {
                "technical_level": "beginner",
                "communication_style": "friendly",
                "detail_preference": "medium",
                "visualization_preference": "medium",
                "confidence": 0.5,
                "error": str(e)
            }
    
    @monitor_llm(
        run_name="adapt_response_style",
        metadata={
            "operation_details": {
                "prompt_template": "style_adaptation",
                "max_tokens": 1500,
                "temperature": 0.4,
                "response_format": "text"
            }
        }
    )
    async def adapt_response_style(
        self,
        content: str,
        user_preferences: Dict[str, Any]
    ) -> str:
        """
        Adapt the style of a response to match user preferences.
        
        Args:
            content: Original response content
            user_preferences: User communication preferences
            
        Returns:
            str: Adapted response
            
        Raises:
            Exception: If style adaptation fails
        """
        self.logger.info("Adapting response style to user preferences")
        
        try:
            # Extract style preferences
            technical_level = user_preferences.get("technical_level", "beginner")
            comm_style = user_preferences.get("communication_style", "friendly")
            detail_pref = user_preferences.get("detail_preference", "medium")
            
            # Create prompt for style adaptation
            prompt = f"""
            As a Scrum Master AI, adapt the following response to match the user's communication preferences:

            ORIGINAL RESPONSE:
            {content}

            USER PREFERENCES:
            - Technical Level: {technical_level}
            - Communication Style: {comm_style}
            - Detail Preference: {detail_pref}

            Rewrite the response to match these preferences, ensuring:
            1. The technical complexity matches their level ({technical_level})
            2. The tone matches their preferred style ({comm_style})
            3. The level of detail matches their preference ({detail_pref})
            4. The core information and message remains the same
            
            Your response should only contain the adapted text without any explanation or additional text.
            """

            # Call LLM for style adaptation
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Scrum Master AI with expertise in adapting communication style to match user preferences."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.4  # Slightly higher temperature for natural language variation
            )
            
            self.logger.info("Successfully adapted response style")
            return response_content  # Return raw text response
            
        except Exception as e:
            self.logger.error(f"Error adapting response style: {str(e)}", exc_info=True)
            # Return original content if adaptation fails
            return content
    
    #--------------------------------------------------------------------------
    # Technical Question Answering Methods
    #--------------------------------------------------------------------------
    
    @monitor_llm(
        run_name="answer_technical_question",
        metadata={
            "operation_details": {
                "prompt_template": "question_answering",
                "max_tokens": 1500,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def answer_technical_question(
        self,
        user_question: str,
        project_context: Optional[Dict[str, Any]] = None,
        technical_context: Optional[Dict[str, Any]] = None,
        user_technical_level: str = "beginner"
    ) -> Dict[str, Any]:
        """
        Answer a user's technical question in an appropriate manner.
        
        Args:
            user_question: Question from the user
            project_context: Optional project context
            technical_context: Optional technical details needed for the answer
            user_technical_level: User's technical expertise level
            
        Returns:
            Dict[str, Any]: User-appropriate answer to the question
            
        Raises:
            Exception: If question answering fails
        """
        self.logger.info(f"Answering technical question for {user_technical_level} level user")
        
        try:
            # Format prompt for question answering
            formatted_prompt = format_question_answering_prompt(
                user_question=user_question,
                project_context=project_context,
                technical_context=technical_context,
                user_technical_level=user_technical_level
            )

            # Call LLM for question answering
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Scrum Master AI with expertise in explaining technical concepts clearly."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=1500
            )

            # Parse and validate response
            expected_keys = ["answer", "key_points"]
            answer = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info("Successfully answered technical question")
            return answer
            
        except Exception as e:
            self.logger.error(f"Error answering technical question: {str(e)}", exc_info=True)
            # Return basic answer if it fails
            return {
                "answer": "I'm not able to provide a complete answer to your question at the moment due to a technical issue.",
                "key_points": ["The system encountered an error while generating the answer", "Please try asking your question again or rephrase it"],
                "technical_level_used": user_technical_level,
                "error": str(e)
            }
    
    @monitor_llm(
        run_name="generate_requirements_explanation",
        metadata={
            "operation_details": {
                "prompt_template": "requirements_explanation",
                "max_tokens": 2000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def generate_requirements_explanation(
        self,
        requirements: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]] = None,
        user_technical_level: str = "beginner"
    ) -> Dict[str, Any]:
        """
        Generate a user-friendly explanation of project requirements.
        
        Args:
            requirements: List of project requirements
            user_context: Optional context about the user
            user_technical_level: User's technical expertise level
            
        Returns:
            Dict[str, Any]: User-friendly explanation of requirements
            
        Raises:
            Exception: If explanation generation fails
        """
        self.logger.info(f"Generating requirements explanation for {user_technical_level} level user")
        
        try:
            # Format requirements for the prompt
            requirements_text = ""
            for i, req in enumerate(requirements, 1):
                req_id = req.get("id", f"R{i}")
                req_desc = req.get("description", "Unnamed requirement")
                req_type = req.get("type", "functional")
                req_priority = req.get("priority", "medium")
                
                requirements_text += f"{req_id}: {req_desc} (Type: {req_type}, Priority: {req_priority})\n"
            
            # Create prompt for requirements explanation
            prompt = f"""
            As a Scrum Master AI, explain the following project requirements in a user-friendly way:

            PROJECT REQUIREMENTS:
            {requirements_text}

            USER TECHNICAL LEVEL: {user_technical_level}

            Create a clear, accessible explanation that:
            1. Summarizes the requirements in plain language
            2. Groups related requirements together
            3. Highlights the most important aspects
            4. Explains why these requirements matter to the project
            5. Adjusts the technical level to match the user's expertise

            Format your response as a JSON object with:
            {{
                "summary": "Overall summary of the requirements",
                "requirement_groups": [
                    {{
                        "name": "Group name",
                        "description": "Description of this group",
                        "requirements": ["Simplified explanation of requirement 1", "Simplified explanation of requirement 2"]
                    }}
                ],
                "key_considerations": ["Important aspects to understand"],
                "business_value": "Explanation of why these requirements matter",
                "technical_level_used": "The level of technical detail provided"
            }}
            """

            # Call LLM for requirements explanation
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Scrum Master AI with expertise in explaining project requirements to stakeholders."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000
            )

            # Parse and validate response
            expected_keys = ["summary", "requirement_groups", "key_considerations"]
            explanation = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info("Successfully generated requirements explanation")
            return explanation
            
        except Exception as e:
            self.logger.error(f"Error generating requirements explanation: {str(e)}", exc_info=True)
            # Return basic explanation if it fails
            return {
                "summary": "The project has several requirements that need to be implemented.",
                "requirement_groups": [
                    {
                        "name": "Project Requirements",
                        "description": "Core project requirements",
                        "requirements": ["Due to a system error, detailed requirements explanation couldn't be generated."]
                    }
                ],
                "key_considerations": ["Please check the original requirements documentation"],
                "technical_level_used": user_technical_level,
                "error": str(e)
            }

    @monitor_llm(
        run_name="generate_clarification_questions",
        metadata={
            "operation_details": {
                "prompt_template": "requirement_clarification",
                "max_tokens": 1000,
                "temperature": 0.4,
                "response_format": "structured_json"
            }
        }
    )
    async def generate_clarification_questions(
        self,
        user_input: str,
        request_analysis: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate clarification questions for ambiguous user requests.
        
        Args:
            user_input: Original user input
            request_analysis: Analysis of the user request
            user_preferences: Optional user preferences
            
        Returns:
            Dict[str, Any]: Clarification message and questions
            
        Raises:
            Exception: If question generation fails
        """
        self.logger.info("Generating clarification questions")
        
        try:
            # Format prompt for requirement clarification
            formatted_prompt = format_requirement_clarification_prompt(
                user_input=user_input,
                request_analysis=request_analysis,
                user_preferences=user_preferences
            )

            # Call LLM for requirement clarification
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Scrum Master AI with expertise in extracting clear requirements from users."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=1000,
                temperature=0.4  # Slightly higher temperature for more conversational tone
            )

            # Parse and validate response
            expected_keys = ["message_to_user", "specific_questions"]
            clarification_result = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info(f"Generated {len(clarification_result.get('specific_questions', []))} clarification questions")
            return clarification_result
            
        except Exception as e:
            self.logger.error(f"Error generating clarification questions: {str(e)}", exc_info=True)
            # Return basic questions if it fails
            return {
                "message_to_user": "I'd like to understand your request better. Could you provide more details?",
                "specific_questions": ["Could you explain more about what you're looking for?", "What specific information do you need?"],
                "tone": "conversational but professional",
                "error": str(e)
            }

    #--------------------------------------------------------------------------
    # Technical Translation Methods
    #--------------------------------------------------------------------------
    
    @monitor_llm(
        run_name="translate_technical_content",
        metadata={
            "operation_details": {
                "prompt_template": "technical_translation",
                "max_tokens": 2000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def translate_technical_content(
        self,
        technical_content: Dict[str, Any],
        user_technical_level: str = "beginner",
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Translate technical content into user-friendly language.
        
        Args:
            technical_content: Technical content to translate
            user_technical_level: User's technical expertise level
            user_preferences: Optional user preferences
            
        Returns:
            Dict[str, Any]: Translated technical content
            
        Raises:
            Exception: If translation fails
        """
        self.logger.info(f"Translating technical content for {user_technical_level} level")
        
        try:
            # Format prompt for technical translation
            formatted_prompt = format_technical_translation_prompt(
                technical_content=technical_content,
                user_technical_level=user_technical_level,
                user_preferences=user_preferences
            )

            # Call LLM for technical translation
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Scrum Master AI with expertise in explaining technical concepts to non-technical users."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=2000
            )

            # Parse and validate response
            expected_keys = ["translated_content", "key_points"]
            translation_result = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info("Successfully translated technical content")
            return translation_result
            
        except Exception as e:
            self.logger.error(f"Error translating technical content: {str(e)}", exc_info=True)
            # Return simplified output if it fails
            return {
                "translated_content": "This technical information couldn't be fully translated due to a system error. Please ask for clarification on specific points you'd like explained.",
                "key_points": ["Technical translation encountered an error", "Consider asking about specific aspects instead"],
                "error": str(e)
            }

    #--------------------------------------------------------------------------
    # Feedback Processing Methods
    #--------------------------------------------------------------------------
    
    @monitor_llm(
        run_name="analyze_feedback",
        metadata={
            "operation_details": {
                "prompt_template": "feedback_analysis",
                "max_tokens": 1500,
                "temperature": 0.2,
                "response_format": "structured_json"
            }
        }
    )
    async def analyze_feedback(
        self,
        user_feedback: str,
        project_context: Dict[str, Any],
        previous_feedback: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze and categorize user feedback.
        
        Args:
            user_feedback: Feedback provided by the user
            project_context: Context about the project
            previous_feedback: Optional history of previous feedback
            
        Returns:
            Dict[str, Any]: Analyzed feedback information
            
        Raises:
            Exception: If feedback analysis fails
        """
        self.logger.info("Analyzing user feedback")
        
        try:
            # Format prompt for feedback analysis
            formatted_prompt = format_feedback_analysis_prompt(
                user_feedback=user_feedback,
                project_context=project_context,
                previous_feedback=previous_feedback
            )

            # Call LLM for feedback analysis
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Scrum Master AI with expertise in analyzing and categorizing user feedback."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=1500,
                temperature=0.2  # Lower temperature for more consistent analysis
            )

            # Parse and validate response
            expected_keys = ["feedback_type", "components", "priority", "sentiment", "key_points"]
            feedback_analysis = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info(f"Analyzed feedback as type: {feedback_analysis.get('feedback_type', 'unknown')}")
            return feedback_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing feedback: {str(e)}", exc_info=True)
            # Return basic analysis if it fails
            return {
                "feedback_type": "general",
                "components": [],
                "priority": "MEDIUM",
                "sentiment": "neutral",
                "key_points": ["User provided feedback", "Analysis error occurred"],
                "actionable": False,
                "error": str(e)
            }

    @monitor_llm(
        run_name="generate_feedback_response",
        metadata={
            "operation_details": {
                "prompt_template": "feedback_response",
                "max_tokens": 1000,
                "temperature": 0.5,
                "response_format": "structured_json"
            }
        }
    )
    async def generate_feedback_response(
        self,
        user_feedback: str,
        feedback_analysis: Dict[str, Any],
        implementation_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a response to user feedback.
        
        Args:
            user_feedback: Original user feedback
            feedback_analysis: Analysis of the feedback
            implementation_status: Optional status of implementation
            
        Returns:
            Dict[str, Any]: Response to the user feedback
            
        Raises:
            Exception: If response generation fails
        """
        self.logger.info("Generating feedback response")
        
        try:
            # Create prompt for feedback response
            prompt = f"""
            As a Scrum Master AI, generate a response to the following user feedback:

            USER FEEDBACK:
            {user_feedback}

            FEEDBACK ANALYSIS:
            Type: {feedback_analysis.get('feedback_type', 'general')}
            Priority: {feedback_analysis.get('priority', 'MEDIUM')}
            Sentiment: {feedback_analysis.get('sentiment', 'neutral')}
            """
            
            if implementation_status:
                prompt += f"\nIMPLEMENTATION STATUS: {implementation_status}"
            
            prompt += """
            Create a thoughtful, empathetic response that:
            1. Acknowledges the user's feedback
            2. Shows you understand their perspective
            3. Explains what will happen with their feedback
            4. Provides next steps or expectations

            Format your response as a JSON object with:
            {
                "response_message": "The full response message to the user",
                "acknowledgment": "Specific acknowledgment of their feedback",
                "next_steps": "What will happen with this feedback",
                "follow_up_questions": ["Optional questions to gather more information if needed"]
            }
            """

            # Call LLM for feedback response
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Scrum Master AI with expertise in responding to user feedback professionally and empathetically."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.5  # Higher temperature for more conversational response
            )

            # Parse and validate response
            expected_keys = ["response_message", "acknowledgment", "next_steps"]
            response = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info("Generated feedback response")
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating feedback response: {str(e)}", exc_info=True)
            # Return basic response if it fails
            return {
                "response_message": "Thank you for your feedback. We've recorded it and will consider it in our development process.",
                "acknowledgment": "Your feedback has been received",
                "next_steps": "Your feedback will be reviewed by the team",
                "error": str(e)
            }

    #--------------------------------------------------------------------------
    # Milestone Communication Methods
    #--------------------------------------------------------------------------
    
    @monitor_llm(
        run_name="create_milestone_presentation",
        metadata={
            "operation_details": {
                "prompt_template": "milestone_presentation",
                "max_tokens": 2500,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def create_milestone_presentation(
        self,
        milestone_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None,
        project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a user-friendly presentation for a technical milestone.
        
        Args:
            milestone_data: Technical milestone data
            user_preferences: Optional user preferences
            project_context: Optional project context
            
        Returns:
            Dict[str, Any]: User-friendly milestone presentation
            
        Raises:
            Exception: If presentation creation fails
        """
        self.logger.info(f"Creating milestone presentation for milestone {milestone_data.get('id', 'unknown')}")
        
        try:
            # Format prompt for milestone presentation
            formatted_prompt = format_milestone_presentation_prompt(
                milestone_data=milestone_data,
                user_preferences=user_preferences,
                project_context=project_context
            )

            # Call LLM for milestone presentation
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Scrum Master AI with expertise in presenting technical milestones to non-technical stakeholders."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=2500
            )

            # Parse and validate response
            expected_keys = ["title", "summary", "key_achievements", "value_delivered", "next_steps"]
            presentation = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info("Successfully created milestone presentation")
            return presentation
            
        except Exception as e:
            self.logger.error(f"Error creating milestone presentation: {str(e)}", exc_info=True)
            # Return basic presentation if it fails
            return {
                "title": milestone_data.get("name", "Project Milestone"),
                "summary": "This milestone represents progress in the project. Due to a system error, detailed presentation couldn't be generated.",
                "key_achievements": ["Milestone reached"],
                "value_delivered": "Progress toward project completion",
                "next_steps": ["Continue project execution"],
                "error": str(e)
            }

    @monitor_llm(
        run_name="prepare_approval_request",
        metadata={
            "operation_details": {
                "prompt_template": "approval_request",
                "max_tokens": 1500,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def prepare_approval_request(
        self,
        milestone_data: Dict[str, Any],
        approval_context: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Prepare a user-friendly approval request for a milestone.
        
        Args:
            milestone_data: Technical milestone data
            approval_context: Context for the approval request
            user_preferences: Optional user preferences
            
        Returns:
            Dict[str, Any]: Formatted approval request
            
        Raises:
            Exception: If approval request creation fails
        """
        self.logger.info(f"Preparing approval request for milestone {milestone_data.get('id', 'unknown')}")
        
        try:
            # Create prompt for approval request
            prompt = f"""
            As a Scrum Master AI, prepare a user-friendly approval request for the following milestone:

            MILESTONE INFORMATION:
            Name: {milestone_data.get('name', 'Project Milestone')}
            Description: {milestone_data.get('description', 'Milestone in the project')}
            Completion: {milestone_data.get('completion_percentage', 0)}%

            APPROVAL CONTEXT:
            Request Purpose: {approval_context.get('purpose', 'Milestone completion approval')}
            Deadline: {approval_context.get('deadline', 'As soon as possible')}
            Impact: {approval_context.get('impact', 'Required to proceed with the project')}

            Create a clear, concise approval request that:
            1. Explains what the user is being asked to approve
            2. Summarizes the key achievements and value
            3. Outlines the consequences of approval or rejection
            4. Provides clear options for the user to choose from

            Format your response as a JSON object with:
            {
                "title": "Concise title for the approval request",
                "description": "Clear explanation of what is being approved",
                "key_points": ["List of important points for the user to consider"],
                "options": [
                    {
                        "id": "option_id",
                        "label": "User-friendly option label",
                        "description": "What this option means",
                        "consequence": "Result of selecting this option"
                    }
                ],
                "recommendation": "Optional recommended action for the user",
                "additional_information": "Any other details the user should know"
            }
            """

            # Call LLM for approval request
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Scrum Master AI with expertise in preparing approval requests for project milestones."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500
            )

            # Parse and validate response
            expected_keys = ["title", "description", "key_points", "options"]
            approval_request = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info("Successfully prepared approval request")
            return approval_request
            
        except Exception as e:
            self.logger.error(f"Error preparing approval request: {str(e)}", exc_info=True)
            # Return basic approval request if it fails
            return {
                "title": f"Approval Needed: {milestone_data.get('name', 'Project Milestone')}",
                "description": "Your approval is needed to proceed with the project.",
                "key_points": ["Milestone has been reached", "Your approval is required to continue"],
                "options": [
                    {
                        "id": "approve",
                        "label": "Approve",
                        "description": "Accept this milestone",
                        "consequence": "Project will proceed to the next phase"
                    },
                    {
                        "id": "reject",
                        "label": "Reject",
                        "description": "Reject this milestone",
                        "consequence": "Project will be revised based on your feedback"
                    }
                ],
                "error": str(e)
            }

    #--------------------------------------------------------------------------
    # Progress Communication Methods
    #--------------------------------------------------------------------------
    
    @monitor_llm(
        run_name="generate_status_report",
        metadata={
            "operation_details": {
                "prompt_template": "status_report",
                "max_tokens": 2000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def generate_status_report(
        self,
        project_status: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None,
        report_type: str = "standard"
    ) -> Dict[str, Any]:
        """
        Generate a user-friendly status report for a project.
        
        Args:
            project_status: Technical project status data
            user_preferences: Optional user preferences
            report_type: Type of report (standard, brief, detailed)
            
        Returns:
            Dict[str, Any]: Formatted status report
            
        Raises:
            Exception: If status report generation fails
        """
        self.logger.info(f"Generating {report_type} status report")
        
        try:
            # Format prompt for status report
            formatted_prompt = format_status_report_prompt(
                project_status=project_status,
                user_preferences=user_preferences,
                report_type=report_type
            )

            # Call LLM for status report
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Scrum Master AI with expertise in creating clear project status reports."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=2000
            )

            # Parse and validate response
            expected_keys = ["report_title", "summary", "progress_overview", "key_achievements", "issues_and_risks"]
            status_report = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info(f"Successfully generated {report_type} status report")
            return status_report
            
        except Exception as e:
            self.logger.error(f"Error generating status report: {str(e)}", exc_info=True)
            # Return basic status report if it fails
            return {
                "report_title": "Project Status Update",
                "summary": "The project is in progress.",
                "progress_overview": f"Current progress: {project_status.get('overall_progress', 0)}%",
                "key_achievements": ["Project continues to move forward"],
                "issues_and_risks": ["Status report generation encountered an error"],
                "upcoming_work": "Continuing project execution",
                "error": str(e)
            }

    @monitor_llm(
        run_name="explain_delays",
        metadata={
            "operation_details": {
                "prompt_template": "delay_explanation",
                "max_tokens": 1000,
                "temperature": 0.4,
                "response_format": "structured_json"
            }
        }
    )
    async def explain_delays(
        self,
        delay_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Explain project delays in a user-friendly manner.
        
        Args:
            delay_data: Technical data about the delay
            user_preferences: Optional user preferences
            
        Returns:
            Dict[str, Any]: User-friendly explanation of delays
            
        Raises:
            Exception: If explanation generation fails
        """
        self.logger.info("Generating delay explanation")
        
        try:
            # Create prompt for delay explanation
            prompt = f"""
            As a Scrum Master AI, explain the following project delay in a user-friendly manner:

            DELAY INFORMATION:
            Type: {delay_data.get('type', 'Schedule delay')}
            Impact: {delay_data.get('impact_days', 0)} days
            Affected Areas: {', '.join(delay_data.get('affected_areas', ['Project timeline']))}
            Technical Reason: {delay_data.get('technical_reason', 'Implementation challenges')}

            Create a clear, understandable explanation that:
            1. Explains the delay without technical jargon
            2. Provides context for why this happened
            3. Outlines the impact on the project
            4. Describes what is being done to address it
            5. Sets expectations for recovery

            Format your response as a JSON object with:
            {{
                "explanation": "User-friendly explanation of the delay",
                "context": "Background information to help understand the situation",
                "impact": "How this affects the project timeline and deliverables",
                "mitigation_steps": ["Actions being taken to address the delay"],
                "revised_expectations": "Updated timeline or expectations",
                "confidence_level": "Confidence in the recovery plan (high/medium/low)"
            }}
            """

            # Call LLM for delay explanation
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Scrum Master AI with expertise in explaining project delays to stakeholders."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.4  # Slightly higher temperature for more natural explanation
            )

            # Parse and validate response
            expected_keys = ["explanation", "impact", "mitigation_steps"]
            explanation = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info("Successfully generated delay explanation")
            return explanation
            
        except Exception as e:
            self.logger.error(f"Error explaining delays: {str(e)}", exc_info=True)
            # Return basic explanation if it fails
            return {
                "explanation": f"The project is experiencing a delay of approximately {delay_data.get('impact_days', 'several')} days.",
                "context": "Technical challenges have affected the timeline.",
                "impact": "This will push back the expected completion date.",
                "mitigation_steps": ["The team is working to address these issues"],
                "revised_expectations": "An updated timeline will be provided soon.",
                "error": str(e)
            }