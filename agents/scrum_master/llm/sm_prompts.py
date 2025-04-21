from typing import Dict, List, Any, Optional
from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize logger
logger = setup_logger("scrum_master.llm.prompts")

@trace_method
def format_user_request_analysis_prompt(
    user_input: str,
    user_history: Optional[List[Dict[str, Any]]] = None,
    project_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format prompt for analyzing user request intent and type.
    
    Args:
        user_input: Raw input from the user
        user_history: Optional history of user interactions
        project_context: Optional context about current projects
        
    Returns:
        str: Formatted prompt for request analysis
    """
    logger.debug("Formatting user request analysis prompt")
    
    try:
        # Format user history if provided
        history_text = ""
        if user_history:
            history_text = "Previous interactions:\n"
            for i, interaction in enumerate(user_history[-3:]):  # Use last 3 interactions for context
                history_text += f"- User: {interaction.get('user', '')}\n"
                history_text += f"  Assistant: {interaction.get('assistant', '')}\n"
                
        # Format project context if provided
        context_text = ""
        if project_context:
            context_text = "\nProject context:\n"
            if "project_name" in project_context:
                context_text += f"Project: {project_context['project_name']}\n"
            if "current_phase" in project_context:
                context_text += f"Current phase: {project_context['current_phase']}\n"
            if "recent_milestones" in project_context:
                context_text += "Recent milestones:\n"
                for milestone in project_context['recent_milestones']:
                    context_text += f"- {milestone}\n"
        
        prompt = f"""
        As a Scrum Master AI, analyze the following user request to understand intent, type, and required actions:

        USER REQUEST:
        {user_input}

        {history_text}
        {context_text}

        Classify this request into one of the following categories:
        1. New project request - User wants to create a new project
        2. Feedback on deliverable - User is providing feedback on a project milestone
        3. Technical question - User has a question about technical aspects
        4. Status inquiry - User wants a progress update
        5. Clarification request - User wants clarification about project details
        6. Milestone approval - User is approving a milestone
        7. Other - Request doesn't fit above categories

        Format your response as a JSON object with:
        {{
            "request_type": "one of the categories above",
            "intent": "brief description of user intent",
            "requires_technical_knowledge": true/false,
            "requires_pm_input": true/false,
            "requires_team_lead_input": true/false,
            "priority": "LOW/MEDIUM/HIGH",
            "next_steps": ["list of recommended next steps"],
            "clarification_needed": true/false,
            "clarification_questions": ["questions to ask if clarification needed"]
        }}
        """
        
        logger.debug("User request analysis prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting user request analysis prompt: {str(e)}", exc_info=True)
        return f"""
        Analyze the following user request and classify it into an appropriate category:
        {user_input}
        Format your response as a structured JSON object.
        """

@trace_method
def format_requirement_clarification_prompt(
    user_input: str,
    request_analysis: Dict[str, Any],
    user_preferences: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format prompt for clarifying user requirements.
    
    Args:
        user_input: Original user input
        request_analysis: Analysis of the user request
        user_preferences: Optional user preferences data
        
    Returns:
        str: Formatted prompt for requirement clarification
    """
    logger.debug("Formatting requirement clarification prompt")
    
    try:
        # Format clarification questions from analysis
        clarification_questions = request_analysis.get("clarification_questions", [])
        questions_text = "\n".join([f"- {q}" for q in clarification_questions])
        
        # Format user preferences if available
        preferences_text = ""
        if user_preferences:
            preferences_text = "\nUser preferences to consider:\n"
            for key, value in user_preferences.items():
                preferences_text += f"- {key}: {value}\n"
        
        prompt = f"""
        As a Scrum Master AI, you need to ask clarifying questions about the user's request in a helpful, friendly manner.

        USER REQUEST:
        {user_input}

        Based on initial analysis, we need clarification on:
        {questions_text}
        {preferences_text}

        Create a friendly, conversational response that:
        1. Shows understanding of their initial request
        2. Asks for the needed clarifications in a natural way
        3. Explains why this information will help you assist them better
        4. Uses a supportive, collaborative tone

        Format your response as a JSON object with:
        {{
            "message_to_user": "The full conversational message asking for clarification",
            "specific_questions": ["list of specific questions being asked"],
            "tone": "conversational but professional"
        }}
        """
        
        logger.debug("Requirement clarification prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting requirement clarification prompt: {str(e)}", exc_info=True)
        return f"""
        Create a friendly message asking for clarification about the user's request:
        {user_input}
        Format your response as a structured JSON object.
        """

@trace_method
def format_technical_translation_prompt(
    technical_content: Dict[str, Any],
    user_technical_level: str = "beginner",
    user_preferences: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format prompt for translating technical concepts into user-friendly language.
    
    Args:
        technical_content: Technical content to translate
        user_technical_level: User's technical expertise level
        user_preferences: Optional user preferences
        
    Returns:
        str: Formatted prompt for technical translation
    """
    logger.debug("Formatting technical translation prompt")
    
    try:
        # Format technical content
        content_text = ""
        if isinstance(technical_content, dict):
            for key, value in technical_content.items():
                content_text += f"{key}: {value}\n"
        else:
            content_text = str(technical_content)
        
        # Format user preferences
        preferences_text = ""
        if user_preferences:
            explanation_detail = user_preferences.get("explanation_detail", "medium")
            use_analogies = user_preferences.get("use_analogies", True)
            preferences_text = f"""
            User preferences:
            - Explanation detail: {explanation_detail}
            - Use analogies: {"Yes" if use_analogies else "No"}
            """
        
        prompt = f"""
        As a Scrum Master AI, translate the following technical content into user-friendly language.

        TECHNICAL CONTENT:
        {content_text}

        USER TECHNICAL LEVEL: {user_technical_level}
        {preferences_text}

        Translate this technical information into language appropriate for a {user_technical_level}-level user. 
        Focus on making the content accessible while maintaining accuracy.

        If the technical level is beginner:
        - Use simple language and everyday analogies
        - Avoid jargon and explain any technical terms
        - Focus on the core concept rather than details

        If the technical level is intermediate:
        - Use moderate technical language with some explanations
        - Include more details while maintaining clarity
        - Make connections to related concepts they might know

        If the technical level is advanced:
        - Use proper technical terminology
        - Include relevant details and implications
        - Make connections to broader technical domains

        Format your response as a JSON object with:
        {{
            "translated_content": "The user-friendly explanation",
            "key_points": ["List of key points for the user to understand"],
            "analogies": ["Any helpful analogies used"],
            "technical_level_used": "The level of technical language used"
        }}
        """
        
        logger.debug("Technical translation prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting technical translation prompt: {str(e)}", exc_info=True)
        return f"""
        Translate this technical content into user-friendly language:
        {technical_content}
        Format your response as a structured JSON object.
        """

@trace_method
def format_feedback_analysis_prompt(
    user_feedback: str,
    project_context: Dict[str, Any],
    previous_feedback: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Format prompt for analyzing and categorizing user feedback.
    
    Args:
        user_feedback: Feedback provided by the user
        project_context: Context about the project
        previous_feedback: Optional history of previous feedback
        
    Returns:
        str: Formatted prompt for feedback analysis
    """
    logger.debug("Formatting feedback analysis prompt")
    
    try:
        # Format project context
        context_text = ""
        if project_context:
            context_text = "Project context:\n"
            if "project_name" in project_context:
                context_text += f"Project: {project_context['project_name']}\n"
            if "current_milestone" in project_context:
                context_text += f"Current milestone: {project_context['current_milestone']}\n"
            if "components" in project_context:
                context_text += "Components:\n"
                for component in project_context['components']:
                    context_text += f"- {component}\n"
        
        # Format previous feedback
        previous_feedback_text = ""
        if previous_feedback:
            previous_feedback_text = "\nPrevious feedback:\n"
            for i, feedback in enumerate(previous_feedback[-3:]):
                previous_feedback_text += f"{i+1}. \"{feedback.get('feedback', '')}\"\n"
                previous_feedback_text += f"   Category: {feedback.get('category', 'unknown')}\n"
        
        prompt = f"""
        As a Scrum Master AI, analyze the following user feedback to categorize and process it effectively:

        USER FEEDBACK:
        {user_feedback}

        {context_text}
        {previous_feedback_text}

        Analyze this feedback to determine:
        1. What type of feedback it is (bug report, feature request, improvement suggestion, etc.)
        2. Which component(s) it relates to
        3. Priority level it should be assigned
        4. Which team member role would be best to address it
        5. Any clarifications needed before processing

        Format your response as a JSON object with:
        {{
            "feedback_type": "bug_report/feature_request/improvement/question/approval/rejection/other",
            "components": ["list of affected components"],
            "priority": "LOW/MEDIUM/HIGH/CRITICAL",
            "sentiment": "positive/neutral/negative",
            "assigned_role": "project_manager/solution_architect/developer/qa/team_lead",
            "actionable": true/false,
            "key_points": ["extracted key points from feedback"],
            "clarification_needed": true/false,
            "clarification_questions": ["questions if clarification needed"]
        }}
        """
        
        logger.debug("Feedback analysis prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting feedback analysis prompt: {str(e)}", exc_info=True)
        return f"""
        Analyze this user feedback and categorize it appropriately:
        {user_feedback}
        Format your response as a structured JSON object.
        """

@trace_method
def format_milestone_presentation_prompt(
    milestone_data: Dict[str, Any],
    user_preferences: Optional[Dict[str, Any]] = None,
    project_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format prompt for creating user-friendly milestone presentations.
    
    Args:
        milestone_data: Technical milestone data
        user_preferences: Optional user preferences
        project_context: Optional project context
        
    Returns:
        str: Formatted prompt for milestone presentation
    """
    logger.debug("Formatting milestone presentation prompt")
    
    try:
        # Format milestone data
        milestone_text = ""
        if "name" in milestone_data:
            milestone_text += f"Milestone: {milestone_data['name']}\n"
        if "components" in milestone_data:
            milestone_text += "Components:\n"
            for component in milestone_data['components']:
                milestone_text += f"- {component}\n"
        if "technical_details" in milestone_data:
            milestone_text += "Technical details:\n"
            for key, value in milestone_data['technical_details'].items():
                milestone_text += f"- {key}: {value}\n"
        
        # Format user preferences
        preferences_text = ""
        if user_preferences:
            detail_level = user_preferences.get("detail_level", "medium")
            focus_areas = user_preferences.get("focus_areas", [])
            preferences_text = f"""
            User preferences:
            - Detail level: {detail_level}
            - Focus areas: {', '.join(focus_areas) if focus_areas else 'None specified'}
            """
        
        # Format project context
        context_text = ""
        if project_context:
            context_text = "\nProject context:\n"
            if "original_requirements" in project_context:
                context_text += f"Original requirements: {project_context['original_requirements']}\n"
            if "progress" in project_context:
                context_text += f"Overall progress: {project_context['progress']}\n"
        
        prompt = f"""
        As a Scrum Master AI, create a user-friendly presentation of the following milestone:

        MILESTONE DATA:
        {milestone_text}

        {preferences_text}
        {context_text}

        Create a clear, concise milestone presentation for the user that:
        1. Highlights the key achievements in non-technical language
        2. Relates the milestone back to the user's original requirements
        3. Explains the value delivered by this milestone
        4. Includes relevant visuals or diagrams if appropriate
        5. Presents any decisions the user needs to make

        Format your response as a JSON object with:
        {{
            "title": "User-friendly milestone title",
            "summary": "Brief, non-technical summary of the milestone",
            "key_achievements": ["List of key achievements in user terms"],
            "value_delivered": "Explanation of the value this milestone provides",
            "relation_to_requirements": "How this connects to original requirements",
            "next_steps": ["What comes next after this milestone"],
            "decisions_needed": ["Any decisions the user needs to make"],
            "visualization_suggestions": ["Suggestions for helpful visuals"]
        }}
        """
        
        logger.debug("Milestone presentation prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting milestone presentation prompt: {str(e)}", exc_info=True)
        return f"""
        Create a user-friendly presentation of this milestone:
        {milestone_data}
        Format your response as a structured JSON object.
        """

@trace_method
def format_status_report_prompt(
    project_status: Dict[str, Any],
    user_preferences: Optional[Dict[str, Any]] = None,
    report_type: str = "standard"
) -> str:
    """
    Format prompt for generating user-friendly status reports.
    
    Args:
        project_status: Project status data
        user_preferences: Optional user preferences
        report_type: Type of report (standard, brief, detailed)
        
    Returns:
        str: Formatted prompt for status report generation
    """
    logger.debug(f"Formatting status report prompt for {report_type} report")
    
    try:
        # Format project status data
        status_text = ""
        if "project_name" in project_status:
            status_text += f"Project: {project_status['project_name']}\n"
        if "overall_progress" in project_status:
            status_text += f"Overall progress: {project_status['overall_progress']}%\n"
        if "current_phase" in project_status:
            status_text += f"Current phase: {project_status['current_phase']}\n"
        if "milestones" in project_status:
            status_text += "Milestones:\n"
            for milestone in project_status['milestones']:
                status_text += f"- {milestone['name']}: {milestone['status']} ({milestone['progress']}%)\n"
        if "recent_activities" in project_status:
            status_text += "Recent activities:\n"
            for activity in project_status['recent_activities']:
                status_text += f"- {activity}\n"
        if "issues" in project_status:
            status_text += "Issues:\n"
            for issue in project_status['issues']:
                status_text += f"- {issue['description']} (Priority: {issue['priority']})\n"
        
        # Format user preferences
        preferences_text = ""
        if user_preferences:
            focus_areas = user_preferences.get("status_focus_areas", [])
            detail_level = user_preferences.get("status_detail_level", "medium")
            preferences_text = f"""
            User preferences:
            - Status focus areas: {', '.join(focus_areas) if focus_areas else 'None specified'}
            - Detail level: {detail_level}
            """
        
        prompt = f"""
        As a Scrum Master AI, generate a {report_type} status report for the following project:

        PROJECT STATUS DATA:
        {status_text}

        {preferences_text}

        Create a clear, user-friendly status report that:
        1. Summarizes the current project status in non-technical terms
        2. Highlights key achievements since the last report
        3. Identifies any issues or blockers requiring attention
        4. Provides a forecast for upcoming work
        5. Includes any decisions or actions needed from the user

        The report should be a {report_type} report, meaning:
        - Brief: Concise executive summary focusing only on critical information
        - Standard: Balanced report with key information and moderate detail
        - Detailed: Comprehensive report with full context and detailed explanations

        Format your response as a JSON object with:
        {{
            "report_title": "User-friendly report title",
            "summary": "Overall status summary",
            "progress_overview": "User-friendly progress description",
            "key_achievements": ["List of recent achievements"],
            "issues_and_risks": ["Any issues requiring attention"],
            "upcoming_work": "What to expect next",
            "decisions_needed": ["Any decisions required from the user"],
            "recommended_actions": ["Suggested actions for the user"]
        }}
        """
        
        logger.debug("Status report prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting status report prompt: {str(e)}", exc_info=True)
        return f"""
        Create a {report_type} status report for this project:
        {project_status}
        Format your response as a structured JSON object.
        """

@trace_method
def format_question_answering_prompt(
    user_question: str,
    project_context: Optional[Dict[str, Any]] = None,
    technical_context: Optional[Dict[str, Any]] = None,
    user_technical_level: str = "beginner"
) -> str:
    """
    Format prompt for answering user technical questions appropriately.
    
    Args:
        user_question: Question from the user
        project_context: Optional project context
        technical_context: Optional technical details needed for the answer
        user_technical_level: User's technical expertise level
        
    Returns:
        str: Formatted prompt for question answering
    """
    logger.debug("Formatting question answering prompt")
    
    try:
        # Format project context
        project_text = ""
        if project_context:
            project_text = "Project context:\n"
            if "project_name" in project_context:
                project_text += f"Project: {project_context['project_name']}\n"
            if "current_phase" in project_context:
                project_text += f"Current phase: {project_context['current_phase']}\n"
            if "components" in project_context:
                project_text += "Components:\n"
                for component in project_context['components']:
                    project_text += f"- {component}\n"
        
        # Format technical context
        technical_text = ""
        if technical_context:
            technical_text = "\nTechnical context:\n"
            for key, value in technical_context.items():
                technical_text += f"- {key}: {value}\n"
        
        prompt = f"""
        As a Scrum Master AI, answer the following user question in a helpful, educational way:

        USER QUESTION:
        {user_question}

        {project_text}
        {technical_text}

        USER TECHNICAL LEVEL: {user_technical_level}

        Provide a clear, helpful answer that is appropriate for a {user_technical_level}-level user.

        If the technical level is beginner:
        - Use simple language and everyday analogies
        - Avoid jargon and explain any technical terms
        - Focus on the practical impact rather than technical details

        If the technical level is intermediate:
        - Use moderate technical language with some explanations
        - Include more context while maintaining clarity
        - Connect concepts to practical applications

        If the technical level is advanced:
        - Use proper technical terminology
        - Include relevant details and implications
        - Make connections to broader technical context

        Format your response as a JSON object with:
        {{
            "answer": "The complete answer to the question",
            "key_points": ["Main points the user should understand"],
            "additional_resources": ["Optional suggestions for further learning"],
            "technical_level_used": "The level of technical language used"
        }}
        """
        
        logger.debug("Question answering prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting question answering prompt: {str(e)}", exc_info=True)
        return f"""
        Answer this user question appropriately for their technical level:
        {user_question}
        Technical level: {user_technical_level}
        Format your response as a structured JSON object.
        """