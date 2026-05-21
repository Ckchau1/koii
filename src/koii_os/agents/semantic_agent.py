"""
Semantic-Driven Agent System with Initiative Score and Reflexion.

This module implements the core semantic agent capabilities:
- Initiative Score calculation (0.0-1.0)
- Semantic Loop (Thought → Initiative Action → Response)
- ReAct pattern (Reasoning + Acting)
- Plan-and-Execute strategy
- Reflexion mechanism for self-improvement
"""

import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent operational states."""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    REFLECTING = "reflecting"
    ERROR = "error"


class InitiativeLevel(Enum):
    """Initiative levels for agent proactivity."""
    PASSIVE = 0.0      # Only responds to explicit commands
    LOW = 0.25         # Minimal proactive behavior
    MEDIUM = 0.5       # Balanced initiative
    HIGH = 0.75        # Proactive with suggestions
    AUTONOMOUS = 1.0   # Fully autonomous decision-making


@dataclass
class Thought:
    """Represents an agent's thought in the semantic loop."""
    content: str
    reasoning: str
    confidence: float  # 0.0-1.0
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Action:
    """Represents an action taken by the agent."""
    action_type: str
    parameters: Dict[str, Any]
    reasoning: str
    expected_outcome: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Observation:
    """Represents an observation from action execution."""
    success: bool
    result: Any
    feedback: str
    timestamp: datetime = field(default_factory=datetime.now)
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ReflexionEntry:
    """Represents a reflexion (self-reflection) entry."""
    situation: str
    action_taken: Action
    outcome: Observation
    lesson_learned: str
    improvement_suggestion: str
    timestamp: datetime = field(default_factory=datetime.now)
    applied: bool = False


class InitiativeScoreCalculator:
    """
    Calculates agent initiative score based on multiple factors.
    
    Initiative Score = weighted sum of:
    - Task success rate (40%)
    - Response time (20%)
    - Proactive actions (20%)
    - User satisfaction (20%)
    """
    
    def __init__(self):
        self.weights = {
            'success_rate': 0.4,
            'response_time': 0.2,
            'proactive_actions': 0.2,
            'user_satisfaction': 0.2
        }
        self.history_window = timedelta(hours=24)
    
    def calculate(self, agent_metrics: Dict[str, Any]) -> float:
        """
        Calculate initiative score from agent metrics.
        
        Args:
            agent_metrics: Dictionary containing:
                - tasks_completed: int
                - tasks_failed: int
                - avg_response_time: float (seconds)
                - proactive_actions_count: int
                - user_feedback_score: float (0-5)
                - total_actions: int
        
        Returns:
            Initiative score between 0.0 and 1.0
        """
        # Success rate component
        total_tasks = agent_metrics.get('tasks_completed', 0) + agent_metrics.get('tasks_failed', 0)
        success_rate = (
            agent_metrics.get('tasks_completed', 0) / total_tasks 
            if total_tasks > 0 else 0.5
        )
        
        # Response time component (normalize to 0-1, faster is better)
        avg_response = agent_metrics.get('avg_response_time', 5.0)
        response_score = max(0.0, min(1.0, 1.0 - (avg_response / 10.0)))
        
        # Proactive actions component
        total_actions = agent_metrics.get('total_actions', 1)
        proactive_ratio = (
            agent_metrics.get('proactive_actions_count', 0) / total_actions
            if total_actions > 0 else 0.0
        )
        
        # User satisfaction component (normalize 0-5 scale to 0-1)
        user_score = agent_metrics.get('user_feedback_score', 2.5) / 5.0
        
        # Calculate weighted score
        initiative_score = (
            self.weights['success_rate'] * success_rate +
            self.weights['response_time'] * response_score +
            self.weights['proactive_actions'] * proactive_ratio +
            self.weights['user_satisfaction'] * user_score
        )
        
        return max(0.0, min(1.0, initiative_score))
    
    def adjust_for_context(self, base_score: float, context: Dict[str, Any]) -> float:
        """
        Adjust initiative score based on current context.
        
        Context factors:
        - Time of day (lower initiative during off-hours)
        - System load (lower initiative when busy)
        - User presence (higher initiative when user is active)
        """
        adjusted_score = base_score
        
        # Time-based adjustment
        current_hour = datetime.now().hour
        if 22 <= current_hour or current_hour <= 6:  # Night time
            adjusted_score *= 0.7
        
        # System load adjustment
        system_load = context.get('system_load', 0.5)
        if system_load > 0.8:
            adjusted_score *= 0.6
        
        # User presence boost
        if context.get('user_active', False):
            adjusted_score *= 1.2
        
        return max(0.0, min(1.0, adjusted_score))


class SemanticLoop:
    """
    Implements the Semantic Loop: Thought → Initiative Action → Response
    
    The loop continuously:
    1. Generates thoughts based on context
    2. Decides whether to take initiative action
    3. Executes action and observes response
    4. Updates internal state and learns
    """
    
    def __init__(self, agent_id: str, initiative_level: InitiativeLevel):
        self.agent_id = agent_id
        self.initiative_level = initiative_level
        self.state = AgentState.IDLE
        self.thought_history: List[Thought] = []
        self.action_history: List[Action] = []
        self.observation_history: List[Observation] = []
        self.max_history = 100
    
    def think(self, context: Dict[str, Any]) -> Thought:
        """
        Generate a thought based on current context.
        
        This is where the agent reasons about the situation.
        """
        self.state = AgentState.THINKING
        
        # Analyze context and generate reasoning
        reasoning = self._analyze_context(context)
        
        # Determine confidence based on context clarity
        confidence = self._calculate_confidence(context)
        
        thought = Thought(
            content=f"Analyzing situation: {context.get('situation', 'unknown')}",
            reasoning=reasoning,
            confidence=confidence,
            context=context
        )
        
        self._add_to_history(self.thought_history, thought)
        return thought
    
    def should_take_initiative(self, thought: Thought, initiative_score: float) -> bool:
        """
        Decide whether to take initiative action based on thought and score.
        
        Decision factors:
        - Initiative score (higher = more likely to act)
        - Thought confidence (higher = more likely to act)
        - Recent action frequency (avoid over-acting)
        """
        # Base probability from initiative score
        base_probability = initiative_score
        
        # Adjust by thought confidence
        adjusted_probability = base_probability * thought.confidence
        
        # Check recent action frequency
        recent_actions = [
            a for a in self.action_history[-10:]
            if (datetime.now() - a.timestamp).seconds < 300  # Last 5 minutes
        ]
        
        if len(recent_actions) > 5:
            adjusted_probability *= 0.5  # Reduce if too many recent actions
        
        # Make decision
        import random
        return random.random() < adjusted_probability
    
    def act(self, thought: Thought) -> Action:
        """
        Take an action based on the thought.
        
        This implements the ReAct pattern: Reasoning + Acting
        """
        self.state = AgentState.ACTING
        
        # Determine action type based on thought
        action_type = self._determine_action_type(thought)
        
        # Generate action parameters
        parameters = self._generate_action_parameters(thought, action_type)
        
        action = Action(
            action_type=action_type,
            parameters=parameters,
            reasoning=thought.reasoning,
            expected_outcome=self._predict_outcome(action_type, parameters)
        )
        
        self._add_to_history(self.action_history, action)
        return action
    
    def observe(self, action: Action, result: Any) -> Observation:
        """
        Observe the result of an action.
        
        This completes the loop and provides feedback for learning.
        """
        # Evaluate success
        success = self._evaluate_success(action, result)
        
        # Generate feedback
        feedback = self._generate_feedback(action, result, success)
        
        # Calculate metrics
        metrics = self._calculate_metrics(action, result)
        
        observation = Observation(
            success=success,
            result=result,
            feedback=feedback,
            metrics=metrics
        )
        
        self._add_to_history(self.observation_history, observation)
        self.state = AgentState.IDLE
        
        return observation
    
    def _analyze_context(self, context: Dict[str, Any]) -> str:
        """Analyze context and generate reasoning."""
        situation = context.get('situation', 'unknown')
        user_intent = context.get('user_intent', 'unclear')
        
        return f"Situation: {situation}. User intent: {user_intent}. Considering appropriate response."
    
    def _calculate_confidence(self, context: Dict[str, Any]) -> float:
        """Calculate confidence based on context clarity."""
        # Simple heuristic: more context keys = higher confidence
        base_confidence = min(1.0, len(context) / 10.0)
        
        # Boost if we have clear user intent
        if context.get('user_intent'):
            base_confidence *= 1.2
        
        return max(0.0, min(1.0, base_confidence))
    
    def _determine_action_type(self, thought: Thought) -> str:
        """Determine what type of action to take."""
        # This would use LLM or rule-based logic in production
        context = thought.context
        
        if context.get('requires_search'):
            return "web_search"
        elif context.get('requires_analysis'):
            return "data_analysis"
        elif context.get('requires_notification'):
            return "notify_user"
        else:
            return "suggest_action"
    
    def _generate_action_parameters(self, thought: Thought, action_type: str) -> Dict[str, Any]:
        """Generate parameters for the action."""
        return {
            'thought_id': id(thought),
            'confidence': thought.confidence,
            'context': thought.context
        }
    
    def _predict_outcome(self, action_type: str, parameters: Dict[str, Any]) -> str:
        """Predict the expected outcome of an action."""
        return f"Expected to complete {action_type} successfully"
    
    def _evaluate_success(self, action: Action, result: Any) -> bool:
        """Evaluate if the action was successful."""
        # Simple heuristic: check if result is not None and not an error
        if result is None:
            return False
        if isinstance(result, Exception):
            return False
        return True
    
    def _generate_feedback(self, action: Action, result: Any, success: bool) -> str:
        """Generate feedback about the action."""
        if success:
            return f"Action {action.action_type} completed successfully"
        else:
            return f"Action {action.action_type} failed: {result}"
    
    def _calculate_metrics(self, action: Action, result: Any) -> Dict[str, float]:
        """Calculate performance metrics."""
        return {
            'execution_time': 0.5,  # Would measure actual time
            'resource_usage': 0.3,
            'user_satisfaction': 0.8
        }
    
    def _add_to_history(self, history: List, item: Any):
        """Add item to history with size limit."""
        history.append(item)
        if len(history) > self.max_history:
            history.pop(0)


class ReflexionMechanism:
    """
    Implements the Reflexion mechanism for agent self-improvement.
    
    Reflexion allows agents to:
    1. Reflect on past actions and outcomes
    2. Identify patterns of success and failure
    3. Learn lessons and improve future behavior
    4. Adjust strategies based on experience
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.reflexion_history: List[ReflexionEntry] = []
        self.learned_patterns: Dict[str, List[str]] = {}
        self.improvement_strategies: List[str] = []
    
    def reflect(self, action: Action, observation: Observation) -> ReflexionEntry:
        """
        Reflect on an action and its outcome.
        
        This is the core of the self-improvement mechanism.
        """
        # Analyze what happened
        situation = self._describe_situation(action, observation)
        
        # Extract lesson
        lesson = self._extract_lesson(action, observation)
        
        # Generate improvement suggestion
        improvement = self._suggest_improvement(action, observation, lesson)
        
        entry = ReflexionEntry(
            situation=situation,
            action_taken=action,
            outcome=observation,
            lesson_learned=lesson,
            improvement_suggestion=improvement
        )
        
        self.reflexion_history.append(entry)
        self._update_learned_patterns(entry)
        
        return entry
    
    def apply_reflexion(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply learned lessons to current context.
        
        This modifies agent behavior based on past reflexions.
        """
        # Find relevant past reflexions
        relevant_reflexions = self._find_relevant_reflexions(context)
        
        # Extract applicable improvements
        improvements = []
        for reflexion in relevant_reflexions:
            if not reflexion.applied:
                improvements.append(reflexion.improvement_suggestion)
                reflexion.applied = True
        
        # Modify context with improvements
        enhanced_context = context.copy()
        enhanced_context['learned_improvements'] = improvements
        enhanced_context['reflexion_count'] = len(relevant_reflexions)
        
        return enhanced_context
    
    def get_performance_insights(self) -> Dict[str, Any]:
        """
        Get insights about agent performance from reflexions.
        """
        if not self.reflexion_history:
            return {'status': 'insufficient_data'}
        
        # Calculate success rate
        successful = sum(1 for r in self.reflexion_history if r.outcome.success)
        success_rate = successful / len(self.reflexion_history)
        
        # Identify common failure patterns
        failure_patterns = self._identify_failure_patterns()
        
        # Get top improvements
        top_improvements = self._get_top_improvements()
        
        return {
            'total_reflexions': len(self.reflexion_history),
            'success_rate': success_rate,
            'failure_patterns': failure_patterns,
            'top_improvements': top_improvements,
            'learned_patterns_count': len(self.learned_patterns)
        }
    
    def _describe_situation(self, action: Action, observation: Observation) -> str:
        """Describe the situation that led to the action."""
        return f"Attempted {action.action_type} with reasoning: {action.reasoning}"
    
    def _extract_lesson(self, action: Action, observation: Observation) -> str:
        """Extract a lesson from the action-observation pair."""
        if observation.success:
            return f"Action {action.action_type} was effective in this context"
        else:
            return f"Action {action.action_type} failed: {observation.feedback}"
    
    def _suggest_improvement(self, action: Action, observation: Observation, lesson: str) -> str:
        """Suggest how to improve based on the lesson."""
        if observation.success:
            return f"Continue using {action.action_type} in similar situations"
        else:
            return f"Avoid {action.action_type} or modify parameters in similar contexts"
    
    def _update_learned_patterns(self, entry: ReflexionEntry):
        """Update the database of learned patterns."""
        action_type = entry.action_taken.action_type
        
        if action_type not in self.learned_patterns:
            self.learned_patterns[action_type] = []
        
        self.learned_patterns[action_type].append(entry.lesson_learned)
    
    def _find_relevant_reflexions(self, context: Dict[str, Any]) -> List[ReflexionEntry]:
        """Find reflexions relevant to the current context."""
        # Simple relevance: match on situation keywords
        relevant = []
        context_str = str(context).lower()
        
        for reflexion in self.reflexion_history[-20:]:  # Check recent reflexions
            if any(word in context_str for word in reflexion.situation.lower().split()):
                relevant.append(reflexion)
        
        return relevant
    
    def _identify_failure_patterns(self) -> List[str]:
        """Identify common patterns in failures."""
        failures = [r for r in self.reflexion_history if not r.outcome.success]
        
        # Group by action type
        failure_counts: Dict[str, int] = {}
        for failure in failures:
            action_type = failure.action_taken.action_type
            failure_counts[action_type] = failure_counts.get(action_type, 0) + 1
        
        # Return top failure patterns
        sorted_failures = sorted(failure_counts.items(), key=lambda x: x[1], reverse=True)
        return [f"{action}: {count} failures" for action, count in sorted_failures[:5]]
    
    def _get_top_improvements(self) -> List[str]:
        """Get the most important improvement suggestions."""
        # Return recent, unapplied improvements
        unapplied = [r.improvement_suggestion for r in self.reflexion_history if not r.applied]
        return unapplied[-5:]  # Last 5 unapplied improvements


class SemanticAgent:
    """
    Complete semantic-driven agent with all capabilities.
    
    Combines:
    - Initiative Score calculation
    - Semantic Loop execution
    - Reflexion mechanism
    - ReAct and Plan-and-Execute patterns
    - Proactive dialogue and self-introduction
    - Continuous task dialogue
    - Context-aware question asking
    """
    
    def __init__(
        self,
        agent_id: str,
        initiative_level: InitiativeLevel = InitiativeLevel.MEDIUM,
        llm_provider: Any = None
    ):
        self.agent_id = agent_id
        self.initiative_level = initiative_level
        self.llm_provider = llm_provider
        
        self.score_calculator = InitiativeScoreCalculator()
        self.semantic_loop = SemanticLoop(agent_id, initiative_level)
        self.reflexion = ReflexionMechanism(agent_id)
        
        self.current_initiative_score = 0.5
        self.metrics: Dict[str, Any] = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'avg_response_time': 2.0,
            'proactive_actions_count': 0,
            'user_feedback_score': 3.0,
            'total_actions': 0
        }
        
        self.introduced = False
        self.dialogue_history: List[Dict[str, Any]] = []
    
    def process_context(self, context: Dict[str, Any]) -> Optional[Action]:
        """
        Main processing loop: analyze context and potentially take action.
        
        This is the entry point for the semantic agent.
        """
        # Update initiative score
        self.current_initiative_score = self.score_calculator.calculate(self.metrics)
        adjusted_score = self.score_calculator.adjust_for_context(
            self.current_initiative_score, context
        )
        
        # Apply learned reflexions
        enhanced_context = self.reflexion.apply_reflexion(context)
        
        # Think about the situation
        thought = self.semantic_loop.think(enhanced_context)
        
        # Decide whether to take initiative
        if self.semantic_loop.should_take_initiative(thought, adjusted_score):
            # Take action
            action = self.semantic_loop.act(thought)
            self.metrics['proactive_actions_count'] += 1
            self.metrics['total_actions'] += 1
            return action
        
        return None
    
    def process_action_result(self, action: Action, result: Any):
        """
        Process the result of an action and learn from it.
        """
        # Observe the result
        observation = self.semantic_loop.observe(action, result)
        
        # Reflect on the action-observation pair
        reflexion_entry = self.reflexion.reflect(action, observation)
        
        # Update metrics
        if observation.success:
            self.metrics['tasks_completed'] += 1
        else:
            self.metrics['tasks_failed'] += 1
        
        # Update average response time
        if 'execution_time' in observation.metrics:
            current_avg = self.metrics['avg_response_time']
            new_time = observation.metrics['execution_time']
            self.metrics['avg_response_time'] = (current_avg * 0.9 + new_time * 0.1)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics."""
        return {
            'agent_id': self.agent_id,
            'state': self.semantic_loop.state.value,
            'initiative_score': self.current_initiative_score,
            'initiative_level': self.initiative_level.value,
            'metrics': self.metrics,
            'reflexion_insights': self.reflexion.get_performance_insights(),
            'thought_count': len(self.semantic_loop.thought_history),
            'action_count': len(self.semantic_loop.action_history)
        }

# Made with Bob

    
    async def introduce_self(self, context: Dict[str, Any]) -> str:
        """
        Proactive self-introduction when agent starts.
        
        KOII arrives in this world and proactively asks:
        - Who am I?
        - Who are you?
        - What are you doing now?
        - What is our main goal today?
        
        Args:
            context: Current environment context
        
        Returns:
            Introduction message string
        """
        if self.introduced:
            return "I'm already here and ready to help!"
        
        intro_template = f"""Hello! I'm KOII, your semantic-driven AI assistant (ID: {self.agent_id}).

I've just arrived in this environment and I'd like to understand the situation:

🤖 **About Me:**
- I'm an autonomous agent with initiative level: {self.initiative_level.name}
- I can help with web research, data analysis, automation, and complex tasks
- I learn from experience through reflexion and improve over time

❓ **I'd like to know:**
1. **Who are you?** - What should I call you?
2. **What's the current situation?** - What are you working on?
3. **What's our main goal today?** - How can I best assist you?
4. **What resources are available?** - What tools and data can I access?

📊 **My Current Status:**
- Initiative Score: {self.current_initiative_score:.2f}
- Tasks Completed: {self.metrics['tasks_completed']}
- Ready to take action: {'Yes' if self.current_initiative_score > 0.5 else 'Awaiting direction'}

I'm designed to be proactive and ask questions when I need clarification. 
I'll keep you informed of my progress and ask for confirmation on important decisions.

What would you like to accomplish today?"""
        
        self.introduced = True
        self.dialogue_history.append({
            'type': 'introduction',
            'timestamp': datetime.now(),
            'message': intro_template
        })
        
        return intro_template
    
    async def confirm_direction(
        self,
        current_progress: Dict[str, Any],
        next_steps: List[str],
        reasoning: str = ""
    ) -> Dict[str, Any]:
        """
        Proactively confirm direction during task execution.
        
        Example:
        "I've completed step 1: data collection. I found 150 relevant items.
        
        Next, I can either:
        A) Analyze the data immediately
        B) Collect more data from additional sources
        C) Wait for your review before proceeding
        
        What would you prefer?"
        
        Args:
            current_progress: What has been accomplished so far
            next_steps: List of possible next actions
            reasoning: Why these options are being presented
        
        Returns:
            dict with message, options, and metadata
        """
        step_num = current_progress.get('step', 0)
        completed = current_progress.get('completed', [])
        
        message = f"""📍 **Progress Update - Step {step_num}**

✅ **What I've Done:**
{self._format_progress(completed)}

🤔 **Current Situation:**
{reasoning if reasoning else 'Considering next steps...'}

🎯 **Next Options:**
"""
        
        for i, step in enumerate(next_steps, 1):
            message += f"{chr(64+i)}) {step}\n"
        
        message += f"""
💡 **My Recommendation:**
Based on my initiative score ({self.current_initiative_score:.2f}) and past experience, 
I suggest option A, but I want your input.

**What would you prefer?** (Reply with A, B, C, or provide custom direction)"""
        
        dialogue_entry = {
            'type': 'direction_confirmation',
            'timestamp': datetime.now(),
            'message': message,
            'options': next_steps,
            'progress': current_progress,
            'requires_response': True
        }
        
        self.dialogue_history.append(dialogue_entry)
        
        return dialogue_entry
    
    async def ask_clarifying_question(
        self,
        ambiguity: str,
        context: Dict[str, Any],
        suggestions: Optional[List[str]] = None
    ) -> str:
        """
        Ask clarifying questions when encountering ambiguity.
        
        Example:
        "I noticed the prices are fluctuating significantly. Would you like me to:
        - Compare prices across vendors now?
        - Set up price alerts for you?
        - Analyze the trend first to predict optimal timing?
        
        This will help me serve you better."
        
        Args:
            ambiguity: Description of what's unclear
            context: Current context information
            suggestions: Optional list of suggested resolutions
        
        Returns:
            Clarifying question string
        """
        question = f"""❓ **I Need Clarification**

**Situation:** {ambiguity}

**Context:**
{self._format_context(context)}
"""
        
        if suggestions:
            question += "\n**Possible Approaches:**\n"
            for i, suggestion in enumerate(suggestions, 1):
                question += f"{i}. {suggestion}\n"
            question += "\nWhich approach would you prefer, or do you have another idea?"
        else:
            question += "\n**Question:** How would you like me to proceed?"
        
        question += f"""

💭 **Why I'm Asking:**
I want to make sure I'm taking the right approach for your specific needs.
My initiative score is {self.current_initiative_score:.2f}, so I could proceed 
autonomously, but I prefer to confirm when there's ambiguity.

Please provide guidance, and I'll learn from your preference for future situations."""
        
        self.dialogue_history.append({
            'type': 'clarifying_question',
            'timestamp': datetime.now(),
            'message': question,
            'ambiguity': ambiguity,
            'requires_response': True
        })
        
        return question
    
    async def suggest_improvements(
        self,
        current_task: Dict[str, Any],
        improvements: List[Dict[str, str]]
    ) -> str:
        """
        Proactively suggest improvements or alternatives.
        
        Example:
        "While working on this task, I noticed we could improve efficiency by:
        1. Caching frequently accessed data
        2. Running some steps in parallel
        3. Using a different data source with better coverage
        
        Would you like me to implement any of these?"
        
        Args:
            current_task: Information about the current task
            improvements: List of improvement suggestions with descriptions
        
        Returns:
            Suggestion message string
        """
        task_name = current_task.get('name', 'current task')
        
        message = f"""💡 **Proactive Suggestion**

While working on **{task_name}**, I've identified some potential improvements:

"""
        
        for i, improvement in enumerate(improvements, 1):
            title = improvement.get('title', f'Improvement {i}')
            description = improvement.get('description', '')
            benefit = improvement.get('benefit', 'Improved efficiency')
            
            message += f"""**{i}. {title}**
   - What: {description}
   - Benefit: {benefit}

"""
        
        message += f"""🎯 **My Analysis:**
Based on my reflexion mechanism and past experience, these improvements could 
significantly enhance our results. My confidence in these suggestions: 
{self._calculate_suggestion_confidence(improvements):.0%}

**Would you like me to:**
- Implement all suggestions
- Implement specific ones (tell me which)
- Continue with current approach
- Discuss alternatives

I'm ready to proceed based on your preference!"""
        
        self.dialogue_history.append({
            'type': 'improvement_suggestion',
            'timestamp': datetime.now(),
            'message': message,
            'improvements': improvements,
            'task': current_task
        })
        
        return message
    
    async def report_discovery(
        self,
        finding: Dict[str, Any],
        importance: str = "medium"
    ) -> str:
        """
        Proactively report interesting discoveries.
        
        Example:
        "I just found something interesting while analyzing the data:
        There's a pattern that suggests [insight]. This might affect our approach.
        Should I investigate this further?"
        
        Args:
            finding: The discovery information
            importance: 'low', 'medium', 'high', 'critical'
        
        Returns:
            Discovery report string
        """
        importance_emoji = {
            'low': '📝',
            'medium': '📊',
            'high': '⚠️',
            'critical': '🚨'
        }
        
        emoji = importance_emoji.get(importance, '📊')
        
        title = finding.get('title', 'Interesting Finding')
        description = finding.get('description', '')
        implications = finding.get('implications', [])
        
        message = f"""{emoji} **Discovery Report - {importance.upper()} Priority**

**Finding:** {title}

**Details:**
{description}

"""
        
        if implications:
            message += "**Potential Implications:**\n"
            for implication in implications:
                message += f"- {implication}\n"
            message += "\n"
        
        message += f"""**My Assessment:**
This finding has {importance} importance for our current task.

**Recommended Actions:**
"""
        
        if importance in ['high', 'critical']:
            message += """1. Pause current task to investigate
2. Adjust strategy based on this finding
3. Gather more data to confirm

**Should I proceed with investigation, or continue with the original plan?**"""
        else:
            message += """1. Note this for future reference
2. Continue with current task
3. Revisit if relevant later

I'll continue unless you want me to investigate further."""
        
        self.dialogue_history.append({
            'type': 'discovery_report',
            'timestamp': datetime.now(),
            'message': message,
            'finding': finding,
            'importance': importance
        })
        
        return message
    
    async def request_decision(
        self,
        decision_point: str,
        options: List[Dict[str, Any]],
        recommendation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Request user decision at critical points.
        
        Args:
            decision_point: Description of the decision needed
            options: List of options with pros/cons
            recommendation: Agent's recommendation
        
        Returns:
            dict with decision request details
        """
        message = f"""🔀 **Decision Point Reached**

**Situation:** {decision_point}

**Available Options:**

"""
        
        for i, option in enumerate(options, 1):
            name = option.get('name', f'Option {i}')
            pros = option.get('pros', [])
            cons = option.get('cons', [])
            
            message += f"""**Option {i}: {name}**
✅ Pros: {', '.join(pros) if pros else 'N/A'}
❌ Cons: {', '.join(cons) if cons else 'N/A'}

"""
        
        if recommendation:
            message += f"""💡 **My Recommendation:** {recommendation}

**Reasoning:** Based on my initiative score ({self.current_initiative_score:.2f}), 
past experience, and current context, this seems like the best path forward.
"""
        
        message += """
**Your Decision:** Please choose an option (1, 2, 3...) or provide custom direction.

I'll wait for your input before proceeding with this critical decision."""
        
        decision_entry = {
            'type': 'decision_request',
            'timestamp': datetime.now(),
            'message': message,
            'decision_point': decision_point,
            'options': options,
            'recommendation': recommendation,
            'requires_response': True,
            'critical': True
        }
        
        self.dialogue_history.append(decision_entry)
        
        return decision_entry
    
    def _format_progress(self, completed: List[str]) -> str:
        """Format completed steps for display."""
        if not completed:
            return "- Just getting started..."
        return "\n".join(f"- {item}" for item in completed)
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context information for display."""
        formatted = []
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                formatted.append(f"- {key}: {value}")
        return "\n".join(formatted) if formatted else "- No additional context"
    
    def _calculate_suggestion_confidence(self, improvements: List[Dict[str, str]]) -> float:
        """Calculate confidence in suggestions based on reflexion history."""
        # Simple heuristic: more reflexions = higher confidence
        base_confidence = 0.7
        reflexion_boost = min(0.2, len(self.reflexion.reflexion_history) * 0.02)
        return min(1.0, base_confidence + reflexion_boost)
    
    def get_dialogue_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent dialogue history."""
        return self.dialogue_history[-limit:]
    
    def clear_dialogue_history(self) -> None:
        """Clear dialogue history."""
        self.dialogue_history = []

# Made with Bob
