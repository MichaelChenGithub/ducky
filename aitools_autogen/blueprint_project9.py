# filename: blueprint_project9.py

from typing import Optional

from autogen import ConversableAgent

import aitools_autogen.utils
from aitools_autogen.blueprint import Blueprint
from aitools_autogen.config import llm_config_openai as llm_config, config_list_openai as config_list, WORKING_DIR


class CodeQualityAnalyzerBlueprint(Blueprint):
    """Blueprint for generating a code quality analyzer tool."""

    def __init__(self, work_dir: Optional[str] = WORKING_DIR):
        super().__init__([], config_list=config_list, llm_config=llm_config)
        self._work_dir = work_dir or "aitools_autogen/coding"
        self._summary_result: Optional[str] = None

    @property
    def summary_result(self) -> str | None:
        """The getter for the 'summary_result' attribute."""
        return self._summary_result

    @property
    def work_dir(self) -> str:
        """The getter for the 'work_dir' attribute."""
        return self._work_dir

    async def initiate_work(self, message: str):
        """Initialize the code generation process."""
        aitools_autogen.utils.clear_working_dir(self._work_dir)
        
        coordinator = ConversableAgent(
            "coordinator",
            max_consecutive_auto_reply=0,
            llm_config=False,
            human_input_mode="NEVER"
        )

        architect = ConversableAgent(
            "architect",
            max_consecutive_auto_reply=6,
            llm_config=llm_config,
            human_input_mode="NEVER",
            code_execution_config=False,
            system_message="""You are a software architect specializing in Python code quality tools.
            Given a request for a code analysis tool, create a detailed plan for its implementation.
            Focus on modularity, extensibility, and clear separation of concerns.
            Include specific file names and their responsibilities."""
        )

        developer = ConversableAgent(
            "developer",
            max_consecutive_auto_reply=6,
            llm_config=llm_config,
            human_input_mode="NEVER",
            code_execution_config=False,
            system_message="""You are a Python developer expert in creating code analysis tools.
            When given an architecture plan, implement the complete solution with the following guidelines:
            - Use modern Python features and best practices
            - Include proper type hints
            - Write clear docstrings and comments
            - Implement error handling
            - Create modular and testable code
            
            Always include the filename at the start of each code block as:
            # filename: aitools_autogen/coding/<filename>
            
            Implement all necessary files to create a working solution."""
        )

        # Initial request to architect
        prompt = f"""Create a code quality analyzer tool with these requirements:
        1. Analyze Python code for common issues like:
           - Function complexity (cyclomatic complexity)
           - Code duplication
           - Line length violations
           - Import organization
        2. Generate a detailed report in markdown format
        3. Provide suggestions for improvement
        
        Original request: {message}"""

        coordinator.initiate_chat(architect, True, True, message=prompt)
        architecture_plan = coordinator.last_message(architect)["content"]

        # Send architecture plan to developer
        coordinator.initiate_chat(developer, True, True, message=architecture_plan)
        
        # Save generated code files
        implementation = coordinator.last_message(developer)["content"]
        aitools_autogen.utils.save_code_files(implementation, self.work_dir)
        
        # Generate summary of created files
        self._summary_result = aitools_autogen.utils.summarize_files(self.work_dir)