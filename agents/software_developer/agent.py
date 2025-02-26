from typing import Dict, Any
from datetime import datetime
from core.logging.logger import setup_logger
from agents.core.base_agent import BaseAgent
from agents.software_developer.llm.service import LLMService
from memory.memory_manager import MemoryManager
from memory.base import MemoryType  # Added for memory type enum
from langgraph.graph import StateGraph, END
from state_graph import SoftwareDeveloperGraphState

class SoftwareDeveloperAgent(BaseAgent):
    """Software Developer Agent responsible for generating code for front-end, back-end and database LangGraph."""
    
    def __init__(self, agent_id: str, name: str, memory_manager: MemoryManager):
        self.logger = setup_logger(f"software_developer.{agent_id}")
        self.logger.info(f"Initializing Software Developer agent with ID: {agent_id}")
        try:
            super().__init__(agent_id, name, memory_manager)
            self.llm_service = LLMService()
            self.logger.info("Software Developer Agent initialization completed")
        except Exception as e:
            self.logger.error(f"Failed to initialize  Software Developer Agent: {str(e)}", exc_info=True)
            raise
    
    def add_graph_nodes(self, graph: StateGraph) -> None:
        """Defines processing nodes for the Project Manager Agent."""
        self.logger.debug("Adding graph nodes to ProjectManagerAgent")
        try:
            graph.add_node("start", self.receive_input)
            graph.add_node("analyze_requirements", self.analyze_requirements)
            graph.add_node("get_tech_stack", self.get_tech_stack)
            graph.add_node("generate_fronend_code", self.generate_frontend_code)
            graph.add_node("generate_backend_code", self.generate_backend_code)
            graph.add_node("generate_database_code", self.generate_database_code)

            graph.add_edge("start", "analyze_requirements")
            graph.add_edge("analyze_requirements", "get_tech_stack")
            graph.add_edge("get_tech_stack", "generate_fronend_code")
            graph.add_edge("get_tech_stack", "generate_backend_code")
            graph.add_edge("get_tech_stack", "generate_database_code")
            graph.add_edge("generate_fronend_code", END)
            graph.add_edge("generate_backend_code", END)
            graph.add_edge("generate_database_code", END)
            
            self.logger.info("Successfully added all graph nodes and edges")
        except Exception as e:
            self.logger.error(f"Failed to add graph nodes: {str(e)}", exc_info=True)
            raise

    async def receive_input(self, state: SoftwareDeveloperGraphState) -> Dict[str, Any]:
        """Handles project input processing."""
        self.logger.info("Receiving project input")
        try:
            input_data = state["input"]
            
            # Store initial request in short-term memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.SHORT_TERM,
                content={
                    "initial_request": input_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            self.update_status("receiving_project_input")
            return {"input": input_data, "status": "analyzing_requirements"}
        except Exception as e:
            self.logger.error(f"Error processing input: {str(e)}", exc_info=True)
            raise

    async def analyze_requirements(self, state: SoftwareDeveloperGraphState) -> Dict[str, Any]:
        """Analyzes and structures project requirements."""
        self.logger.info("Analyzing project requirements")
        try:
            project_description = state["input"]
            
            # Check working memory for similar previous analysis
            previous_analyses = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                query={"project_description": project_description}
            )
            
            if previous_analyses:
                self.logger.info("Found previous analysis in working memory")
                response = previous_analyses[0].content
            else:
                # Perform new analysis
                response = await self.llm_service.analyze_requirements(project_description)
                
                # Store in working memory for active processing
                await self.memory_manager.store(
                    agent_id=self.agent_id,
                    memory_type=MemoryType.WORKING,
                    content={
                        "project_description": project_description,
                        "requirement_analysis": response,
                        "analysis_timestamp": datetime.utcnow().isoformat()
                    }
                )
            
            # Store in long-term memory for future reference
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content={
                    "project_description": project_description,
                    "requirement_analysis": response,
                    "analysis_timestamp": datetime.utcnow().isoformat()
                },
                metadata={
                    "type": "requirement_analysis",
                    "importance": 0.8
                }
            )
            
            return {"requirements": response, "status": "generating_project_plan"}
            
        except Exception as e:
            self.logger.error(f"Error analyzing requirements: {str(e)}", exc_info=True)
            raise

    async def get_tech_stack(self, state: SoftwareDeveloperGraphState) -> Dict[str, Any]:
        """Get the tech stack for a project based on the project description."""
        self.logger.info("Getting tech stack based on project description")
        try:
            project_description = state["input"]

            # Check working memory for similar previous analysis
            # previous_analyses = await self.memory_manager.retrieve(
            #     agent_id=self.agent_id,
            #     memory_type=MemoryType.WORKING,
            #     query={"project_description": project_description}
            # )
            previous_analyses = None
            if previous_analyses:
                self.logger.info("Found previous analysis in working memory")
                response = previous_analyses[0].content
            else:
                # Perform new analysis
                response = await self.llm_service.get_tech_stack(project_description)
                
                # Store in working memory for active processing
                await self.memory_manager.store(
                    agent_id=self.agent_id,
                    memory_type=MemoryType.WORKING,
                    content={
                        "project_description": project_description,
                        "tech_stack": response,
                        "analysis_timestamp": datetime.utcnow().isoformat()
                    }
                )

            # Store in long-term memory for future reference
            # await self.memory_manager.store(
            #     agent_id=self.agent_id,
            #     memory_type=MemoryType.LONG_TERM,
            #     content={
            #         "project_description": project_description,
            #         "tech_stack": response,
            #         "analysis_timestamp": datetime.utcnow().isoformat()
            #     },
            #     metadata={
            #         "type": "tech_stack",
            #         "importance": 0.8
            #     }
            # )
            return {"tech_stack": response, "status": "generated_tech_stack"}
        except Exception as e:
            self.logger.error(f"Error getting project description: {str(e)}", exc_info=True)
        return None

    async def generate_frontend_code(self, state: SoftwareDeveloperGraphState) -> Dict[str, Any]:
        self.logger.info("Getting frontend conponents based on project requirements")
        try:
            project_description = state["input"]
            requirements = state["requirements"]
            tech_stack = state["tech_stack"]["frontend"]

            # Check working memory for similar previous analysis
            # previous_analyses = await self.memory_manager.retrieve(
            #     agent_id=self.agent_id,
            #     memory_type=MemoryType.WORKING,
            #     query={"project_description": project_description}
            # )
            previous_analyses = None
            if previous_analyses:
                self.logger.info("Found previous analysis in working memory")
                response = previous_analyses[0].content
            else:
                # Perform new analysis
                response = await self.llm_service.get_front_end(requirements, tech_stack)
                
                # Store in working memory for active processing
                await self.memory_manager.store(
                    agent_id=self.agent_id,
                    memory_type=MemoryType.WORKING,
                    content={
                        "project_description": project_description,
                        "tech_stack": response,
                        "analysis_timestamp": datetime.utcnow().isoformat()
                    }
                )
                self.logger
                self.logger.info(response)
        except Exception as e:
            self.logger.error(f"Error getting project description: {str(e)}", exc_info=True)
        return None
    
    async def generate_backend_code(self, state: SoftwareDeveloperGraphState) -> Dict[str, Any]:
        self.logger.info("Getting backend components based on project requirements")
        try:
            project_description = state["input"]
            requirements = state["requirements"]
            tech_stack = state["tech_stack"]["backend"]

            # Check working memory for similar previous analysis
            # previous_analyses = await self.memory_manager.retrieve(
            #     agent_id=self.agent_id,
            #     memory_type=MemoryType.WORKING,
            #     query={"project_description": project_description}
            # )
            previous_analyses = None
            if previous_analyses:
                self.logger.info("Found previous analysis in working memory")
                response = previous_analyses[0].content
            else:
                # Perform new analysis
                response = await self.llm_service.get_back_end(requirements, tech_stack)
                
                # Store in working memory for active processing
                await self.memory_manager.store(
                    agent_id=self.agent_id,
                    memory_type=MemoryType.WORKING,
                    content={
                        "project_description": project_description,
                        "tech_stack": response,
                        "analysis_timestamp": datetime.utcnow().isoformat()
                    }
                )
                self.logger
                self.logger.info(response)
        except Exception as e:
            self.logger.error(f"Error getting project description: {str(e)}", exc_info=True)
        return None

    async def generate_database_code(self, state: SoftwareDeveloperGraphState) -> Dict[str, Any]:
        self.logger.info("Getting database components based on project requirements")
        try:
            project_description = state["input"]
            requirements = state["requirements"]
            tech_stack = state["tech_stack"]["database"]

            # Check working memory for similar previous analysis
            # previous_analyses = await self.memory_manager.retrieve(
            #     agent_id=self.agent_id,
            #     memory_type=MemoryType.WORKING,
            #     query={"project_description": project_description}
            # )
            previous_analyses = None
            if previous_analyses:
                self.logger.info("Found previous analysis in working memory")
                response = previous_analyses[0].content
            else:
                # Perform new analysis
                response = await self.llm_service.get_database(requirements, tech_stack)
                
                # Store in working memory for active processing
                await self.memory_manager.store(
                    agent_id=self.agent_id,
                    memory_type=MemoryType.WORKING,
                    content={
                        "project_description": project_description,
                        "tech_stack": response,
                        "analysis_timestamp": datetime.utcnow().isoformat()
                    }
                )
                self.logger
                self.logger.info(response)
        except Exception as e:
            self.logger.error(f"Error getting project description: {str(e)}", exc_info=True)
        return None