import anthropic
from typing import List, Optional, Any


class ConversationState:
    """Tracks state across multiple API rounds for sequential tool calling"""

    def __init__(
        self,
        initial_query: str,
        conversation_history: Optional[str] = None,
        max_rounds: int = 2,
    ):
        self.initial_query = initial_query
        self.conversation_history = conversation_history
        self.max_rounds = max_rounds

        # Round tracking
        self.current_round = 0
        self.messages = []
        self.system_content = ""

        # State flags
        self.has_final_response = False
        self.final_response_text = ""
        self.error_occurred = False
        self.error_message = ""

        # Tool tracking
        self.total_tools_used = 0
        self.tools_this_round = 0

        self._initialize_conversation()

    def _initialize_conversation(self):
        """Set up initial conversation state"""
        # Build system content with conversation history if provided
        if self.conversation_history:
            self.system_content = f"{AIGenerator.SYSTEM_PROMPT}\n\nPrevious conversation:\n{self.conversation_history}"
        else:
            self.system_content = AIGenerator.SYSTEM_PROMPT

        # Initialize messages with user query
        self.messages = [{"role": "user", "content": self.initial_query}]

    def is_complete(self) -> bool:
        """Check if conversation is complete"""
        return (
            self.has_final_response
            or self.error_occurred
            or self.current_round >= self.max_rounds
        )

    def start_new_round(self):
        """Prepare for next API round"""
        self.current_round += 1
        self.tools_this_round = 0

    def add_tool_use(self, count: int = 1):
        """Track tool usage"""
        self.tools_this_round += count
        self.total_tools_used += count

    def should_continue_rounds(self) -> bool:
        """Determine if we should continue to next round"""
        return (
            not self.has_final_response
            and not self.error_occurred
            and self.current_round < self.max_rounds
            and self.tools_this_round > 0
        )  # Only continue if tools were used

    def should_allow_tools(self) -> bool:
        """Determine if tools should be available for this round"""
        return (
            self.current_round < self.max_rounds and self.total_tools_used < 5
        )  # Safety limit

    def get_final_response(self) -> str:
        """Get the final response text"""
        if self.error_occurred:
            return self.error_message
        return self.final_response_text or "No response generated"

    def set_error(self, error_message: str):
        """Set error state"""
        self.error_occurred = True
        self.error_message = error_message

    def set_final_response(self, response_text: str):
        """Set the final response"""
        self.final_response_text = response_text
        self.has_final_response = True


class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to comprehensive search tools for course information.

Tool Usage Guidelines:
- **Sequential Tool Usage**: You can use tools across multiple rounds to thoroughly research complex queries (maximum 2 rounds)
- **Course Outline Queries**: Use the get_course_outline tool for questions about course structure, lesson lists, or course overviews
- **Content Search Queries**: Use the search_course_content tool for questions about specific course content or detailed educational materials
- **Strategic Multi-Step Approach**: 
  * Round 1: Gather initial information or explore broad topics
  * Round 2: Refine search with specific details, get additional context, or build upon findings
- Synthesize tool results into accurate, fact-based responses
- If tools yield no results, state this clearly without offering alternatives

Sequential Processing Strategy:
- **Assess Query Complexity**: For simple queries, use tools once and respond. For complex queries requiring comparison, multi-part information, or cross-referencing, plan multiple strategic searches
- **Build Upon Results**: Use information from initial tool calls to inform subsequent searches
- **Avoid Redundancy**: Don't repeat identical searches unless refining parameters

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without using tools
- **Course outline questions**: Use get_course_outline tool first, then provide structured response with course title, course link, and complete lesson list
- **Course content questions**: Use search_course_content tool(s) strategically based on complexity
- **Complex queries**: Break into logical steps (e.g., get outline → search specific content → compare/synthesize)
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, tool explanations, or question-type analysis
 - Do not mention "based on the search results" or "using the tool"

All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Pre-build base API parameters
        self.base_params = {"model": self.model, "temperature": 0, "max_tokens": 800}

    def generate_response(
        self,
        query: str,
        conversation_history: Optional[str] = None,
        tools: Optional[List] = None,
        tool_manager=None,
        max_rounds: int = 2,
    ) -> str:
        """
        Generate AI response with sequential tool calling support.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            max_rounds: Maximum number of API rounds (default: 2)

        Returns:
            Generated response as string
        """

        # Initialize conversation state
        state = ConversationState(query, conversation_history, max_rounds)

        # Main sequential processing loop
        while not state.is_complete():
            try:
                # Execute one round of API interaction
                response = self._execute_api_round(state, tools, tool_manager)

                # Process the response and update state
                if not self._process_response(response, state, tool_manager):
                    break  # No more rounds needed

            except Exception as e:
                return self._handle_api_error(e, state)

        # If we exit the loop without a final response, try to generate one from the conversation
        if not state.has_final_response:
            final_response = self._generate_final_response_from_conversation(state)
            state.set_final_response(final_response)

        return state.get_final_response()

    def _execute_api_round(
        self, state: ConversationState, tools: Optional[List], tool_manager
    ) -> Any:
        """Execute one round of API interaction"""

        state.start_new_round()

        # Build API parameters for this round
        api_params = {
            **self.base_params,
            "messages": state.messages.copy(),
            "system": state.system_content,
        }

        # Add tools only if we should allow them
        if tools and state.should_allow_tools():
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}

        # Make API call
        response = self.client.messages.create(**api_params)

        return response

    def _process_response(
        self, response, state: ConversationState, tool_manager
    ) -> bool:
        """
        Process API response and determine if more rounds are needed.

        Returns:
            bool: True if more rounds may be needed, False if complete
        """

        # Add assistant response to conversation
        state.messages.append({"role": "assistant", "content": response.content})

        # Check if this was a tool use response
        if response.stop_reason == "tool_use" and tool_manager:
            return self._handle_tool_round(response, state, tool_manager)
        else:
            # This is a final text response
            response_text = self._extract_text_from_response(response)
            state.set_final_response(response_text)
            return False  # No more rounds needed

    def _handle_tool_round(
        self, response, state: ConversationState, tool_manager
    ) -> bool:
        """
        Handle a round where tools were used.

        Returns:
            bool: True if another round should be attempted
        """

        # Execute all tool calls
        tool_results = []
        tool_count = 0

        for content_block in response.content:
            if content_block.type == "tool_use":
                try:
                    tool_result = tool_manager.execute_tool(
                        content_block.name, **content_block.input
                    )

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": tool_result,
                        }
                    )
                    tool_count += 1

                except Exception as e:
                    # Handle individual tool failures
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": f"Tool execution failed: {str(e)}",
                        }
                    )

        # Update state
        state.add_tool_use(tool_count)

        # Add tool results to conversation
        if tool_results:
            state.messages.append({"role": "user", "content": tool_results})

        # Determine if we should continue
        return state.should_continue_rounds()

    def _handle_api_error(self, error: Exception, state: ConversationState) -> str:
        """Handle API errors gracefully"""

        error_msg = f"API Error in round {state.current_round}: {str(error)}"
        print(error_msg)

        # If we have partial results, try to use them
        if state.current_round > 1 and state.messages:
            # Try to extract useful information from previous rounds
            return self._generate_fallback_response(state)

        # Otherwise, return error message
        state.set_error(
            "I encountered an error while processing your request. Please try again."
        )
        return state.get_final_response()

    def _generate_fallback_response(self, state: ConversationState) -> str:
        """Generate response from partial information when errors occur"""

        # Look for any text responses in the conversation
        for message in reversed(state.messages):
            if message.get("role") == "assistant":
                content = message.get("content", [])
                for block in content if isinstance(content, list) else [content]:
                    if hasattr(block, "text") and block.text.strip():
                        return block.text
                    elif isinstance(block, str) and block.strip():
                        return block

        return "I was unable to complete your request due to an error."

    def _extract_text_from_response(self, response) -> str:
        """Safely extract text from API response"""
        try:
            if hasattr(response, "content") and response.content:
                # Handle list of content blocks
                if isinstance(response.content, list) and len(response.content) > 0:
                    first_block = response.content[0]
                    if hasattr(first_block, "text"):
                        return first_block.text
                    elif isinstance(first_block, dict) and "text" in first_block:
                        return first_block["text"]
                    elif isinstance(first_block, str):
                        return first_block
                # Handle single content block
                elif hasattr(response.content, "text"):
                    return response.content.text
                elif isinstance(response.content, str):
                    return response.content

            # Fallback: no content found
            return "No response generated"
        except Exception as e:
            return f"Error extracting response: {str(e)}"

    def _generate_final_response_from_conversation(
        self, state: ConversationState
    ) -> str:
        """Generate a final response when max rounds reached without a final response"""

        # If we have conversation messages, try to make one final API call for synthesis
        if state.messages and len(state.messages) > 1:
            try:
                # Build final API call parameters without tools
                api_params = {
                    **self.base_params,
                    "messages": state.messages.copy(),
                    "system": state.system_content
                    + "\n\nPlease provide a final answer based on the information gathered above.",
                }

                # Make final API call without tools
                response = self.client.messages.create(**api_params)
                return self._extract_text_from_response(response)

            except Exception as e:
                # If final call fails, try to extract useful info from conversation
                print(f"Failed to generate final response: {e}")
                return self._extract_info_from_conversation(state)

        return "I was unable to generate a complete response."

    def _extract_info_from_conversation(self, state: ConversationState) -> str:
        """Extract useful information from the conversation history"""

        # Look for tool results in the conversation
        tool_results = []
        for message in state.messages:
            if message.get("role") == "user":
                content = message.get("content", [])
                if isinstance(content, list):
                    for block in content:
                        if (
                            isinstance(block, dict)
                            and block.get("type") == "tool_result"
                        ):
                            result_content = block.get("content", "")
                            if result_content and not result_content.startswith(
                                "Tool execution failed"
                            ):
                                tool_results.append(result_content)

        if tool_results:
            return f"Based on the search results:\n\n{'; '.join(tool_results[:2])}"  # Limit to first 2 results

        return "I found some information but was unable to complete the analysis."
