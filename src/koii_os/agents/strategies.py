"""
Agent execution strategies: ReAct and Plan-and-Execute.

This module implements two key agent reasoning patterns:
1. ReAct: Reasoning + Acting in an interleaved manner
2. Plan-and-Execute: Planning first, then executing the plan
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """Status of a plan step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ReActStep:
    """
    A single step in the ReAct pattern.
    
    ReAct alternates between:
    - Thought: Reasoning about what to do
    - Action: Taking an action
    - Observation: Observing the result
    """
    step_number: int
    thought: str
    action: str
    action_input: Dict[str, Any]
    observation: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = False


@dataclass
class PlanStep:
    """A single step in a plan."""
    step_id: str
    description: str
    action_type: str
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Plan:
    """A complete execution plan."""
    plan_id: str
    goal: str
    steps: List[PlanStep]
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    success: bool = False


class ReActStrategy:
    """
    Implements the ReAct (Reasoning + Acting) pattern.
    
    ReAct interleaves reasoning and acting:
    1. Think about what to do next
    2. Take an action
    3. Observe the result
    4. Repeat until goal is achieved
    
    This is more flexible than Plan-and-Execute but may be less efficient.
    """
    
    def __init__(self, agent_id: str, max_steps: int = 10):
        self.agent_id = agent_id
        self.max_steps = max_steps
        self.steps: List[ReActStep] = []
        self.current_step = 0
    
    def execute(self, goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a goal using the ReAct pattern.
        
        Args:
            goal: The goal to achieve
            context: Current context and available information
        
        Returns:
            Result dictionary with success status and final observation
        """
        logger.info(f"[ReAct] Starting execution for goal: {goal}")
        
        self.steps = []
        self.current_step = 0
        
        current_context = context.copy()
        current_context['goal'] = goal
        current_context['steps_taken'] = []
        
        while self.current_step < self.max_steps:
            # Check if goal is achieved
            if self._is_goal_achieved(goal, current_context):
                logger.info(f"[ReAct] Goal achieved in {self.current_step} steps")
                return {
                    'success': True,
                    'steps': self.steps,
                    'final_observation': 'Goal achieved',
                    'steps_taken': self.current_step
                }
            
            # Execute one ReAct step
            step = self._execute_step(goal, current_context)
            self.steps.append(step)
            
            # Update context with observation
            current_context['last_observation'] = step.observation
            current_context['steps_taken'].append({
                'thought': step.thought,
                'action': step.action,
                'observation': step.observation
            })
            
            self.current_step += 1
            
            # Check for failure
            if not step.success:
                logger.warning(f"[ReAct] Step {self.current_step} failed")
                # Decide whether to continue or abort
                if self._should_abort(step, current_context):
                    return {
                        'success': False,
                        'steps': self.steps,
                        'final_observation': f'Aborted after step {self.current_step}',
                        'error': step.observation
                    }
        
        # Max steps reached without achieving goal
        logger.warning(f"[ReAct] Max steps ({self.max_steps}) reached without achieving goal")
        return {
            'success': False,
            'steps': self.steps,
            'final_observation': 'Max steps reached',
            'steps_taken': self.current_step
        }
    
    def _execute_step(self, goal: str, context: Dict[str, Any]) -> ReActStep:
        """Execute a single ReAct step."""
        # Thought: Reason about what to do
        thought = self._generate_thought(goal, context)
        
        # Action: Decide on an action
        action, action_input = self._decide_action(thought, context)
        
        # Execute the action
        observation, success = self._execute_action(action, action_input, context)
        
        return ReActStep(
            step_number=self.current_step + 1,
            thought=thought,
            action=action,
            action_input=action_input,
            observation=observation,
            success=success
        )
    
    def _generate_thought(self, goal: str, context: Dict[str, Any]) -> str:
        """
        Generate a thought about what to do next.
        
        In production, this would use an LLM to reason about the situation.
        """
        steps_taken = len(context.get('steps_taken', []))
        last_obs = context.get('last_observation', 'No previous observation')
        
        if steps_taken == 0:
            return f"I need to achieve: {goal}. Let me start by analyzing the situation."
        else:
            return f"Previous observation: {last_obs}. I should continue working towards: {goal}"
    
    def _decide_action(self, thought: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Decide what action to take based on the thought.
        
        In production, this would use an LLM or rule-based system.
        """
        # Simple heuristic-based decision
        if 'search' in thought.lower() or 'find' in thought.lower():
            return 'search', {'query': context.get('goal', '')}
        elif 'analyze' in thought.lower():
            return 'analyze', {'data': context.get('data', {})}
        elif 'create' in thought.lower():
            return 'create', {'type': 'document'}
        else:
            return 'observe', {'target': 'environment'}
    
    def _execute_action(self, action: str, action_input: Dict[str, Any], 
                       context: Dict[str, Any]) -> Tuple[str, bool]:
        """
        Execute an action and return observation and success status.
        
        In production, this would call actual action executors.
        """
        try:
            # Simulate action execution
            if action == 'search':
                observation = f"Found relevant information about: {action_input.get('query')}"
                success = True
            elif action == 'analyze':
                observation = "Analysis completed successfully"
                success = True
            elif action == 'create':
                observation = f"Created {action_input.get('type')} successfully"
                success = True
            else:
                observation = "Observed current state"
                success = True
            
            return observation, success
        except Exception as e:
            return f"Action failed: {str(e)}", False
    
    def _is_goal_achieved(self, goal: str, context: Dict[str, Any]) -> bool:
        """
        Check if the goal has been achieved.
        
        In production, this would use more sophisticated goal checking.
        """
        steps_taken = len(context.get('steps_taken', []))
        
        # Simple heuristic: goal achieved after 3-5 successful steps
        if steps_taken >= 3:
            last_steps = context['steps_taken'][-3:]
            all_successful = all('successfully' in step.get('observation', '').lower() 
                               for step in last_steps)
            return all_successful
        
        return False
    
    def _should_abort(self, step: ReActStep, context: Dict[str, Any]) -> bool:
        """Decide whether to abort execution after a failed step."""
        # Abort if we've had 3 consecutive failures
        recent_steps = self.steps[-3:] if len(self.steps) >= 3 else self.steps
        consecutive_failures = all(not s.success for s in recent_steps)
        
        return consecutive_failures


class PlanAndExecuteStrategy:
    """
    Implements the Plan-and-Execute pattern.
    
    This strategy:
    1. Creates a complete plan upfront
    2. Executes the plan step by step
    3. Handles dependencies between steps
    4. Can replan if execution fails
    
    More efficient than ReAct but less flexible.
    """
    
    def __init__(self, agent_id: str, allow_replanning: bool = True):
        self.agent_id = agent_id
        self.allow_replanning = allow_replanning
        self.current_plan: Optional[Plan] = None
        self.execution_history: List[Plan] = []
    
    def execute(self, goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a goal using Plan-and-Execute pattern.
        
        Args:
            goal: The goal to achieve
            context: Current context and available information
        
        Returns:
            Result dictionary with success status and execution details
        """
        logger.info(f"[Plan-Execute] Starting execution for goal: {goal}")
        
        # Phase 1: Planning
        plan = self._create_plan(goal, context)
        self.current_plan = plan
        
        # Phase 2: Execution
        result = self._execute_plan(plan, context)
        
        # Phase 3: Replanning if needed
        if not result['success'] and self.allow_replanning:
            logger.info("[Plan-Execute] Execution failed, attempting to replan")
            
            # Update context with failure information
            context['previous_plan'] = plan
            context['failure_reason'] = result.get('error', 'Unknown')
            
            # Create new plan
            new_plan = self._create_plan(goal, context)
            self.current_plan = new_plan
            
            # Try again
            result = self._execute_plan(new_plan, context)
        
        self.execution_history.append(plan)
        return result
    
    def _create_plan(self, goal: str, context: Dict[str, Any]) -> Plan:
        """
        Create a plan to achieve the goal.
        
        In production, this would use an LLM to generate a detailed plan.
        """
        logger.info(f"[Plan-Execute] Creating plan for: {goal}")
        
        # Generate plan steps
        steps = self._generate_plan_steps(goal, context)
        
        plan = Plan(
            plan_id=f"plan_{datetime.now().timestamp()}",
            goal=goal,
            steps=steps
        )
        
        logger.info(f"[Plan-Execute] Created plan with {len(steps)} steps")
        return plan
    
    def _generate_plan_steps(self, goal: str, context: Dict[str, Any]) -> List[PlanStep]:
        """
        Generate the steps needed to achieve the goal.
        
        This is a simplified version. In production, use LLM-based planning.
        """
        steps = []
        
        # Step 1: Gather information
        steps.append(PlanStep(
            step_id="step_1",
            description="Gather necessary information",
            action_type="search",
            parameters={'query': goal}
        ))
        
        # Step 2: Analyze information
        steps.append(PlanStep(
            step_id="step_2",
            description="Analyze gathered information",
            action_type="analyze",
            parameters={'data_source': 'step_1'},
            dependencies=['step_1']
        ))
        
        # Step 3: Take action based on analysis
        steps.append(PlanStep(
            step_id="step_3",
            description="Execute main action",
            action_type="execute",
            parameters={'based_on': 'step_2'},
            dependencies=['step_2']
        ))
        
        # Step 4: Verify result
        steps.append(PlanStep(
            step_id="step_4",
            description="Verify goal achievement",
            action_type="verify",
            parameters={'goal': goal},
            dependencies=['step_3']
        ))
        
        return steps
    
    def _execute_plan(self, plan: Plan, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the plan step by step."""
        logger.info(f"[Plan-Execute] Executing plan: {plan.plan_id}")
        
        completed_steps = set()
        failed_steps = set()
        
        for step in plan.steps:
            # Check if dependencies are met
            if not self._dependencies_met(step, completed_steps, failed_steps):
                logger.warning(f"[Plan-Execute] Skipping step {step.step_id} - dependencies not met")
                step.status = StepStatus.SKIPPED
                continue
            
            # Execute the step
            step.status = StepStatus.IN_PROGRESS
            success, result, error = self._execute_step(step, context)
            
            if success:
                step.status = StepStatus.COMPLETED
                step.result = result
                completed_steps.add(step.step_id)
                logger.info(f"[Plan-Execute] Step {step.step_id} completed successfully")
            else:
                step.status = StepStatus.FAILED
                step.error = error
                failed_steps.add(step.step_id)
                logger.error(f"[Plan-Execute] Step {step.step_id} failed: {error}")
                
                # Decide whether to continue or abort
                if self._should_abort_plan(step, plan):
                    plan.success = False
                    return {
                        'success': False,
                        'plan': plan,
                        'completed_steps': len(completed_steps),
                        'failed_steps': len(failed_steps),
                        'error': f"Plan aborted at step {step.step_id}"
                    }
        
        # Check if plan succeeded
        plan.completed_at = datetime.now()
        plan.success = len(failed_steps) == 0 and len(completed_steps) > 0
        
        return {
            'success': plan.success,
            'plan': plan,
            'completed_steps': len(completed_steps),
            'failed_steps': len(failed_steps)
        }
    
    def _dependencies_met(self, step: PlanStep, completed: set, failed: set) -> bool:
        """Check if all dependencies for a step are met."""
        for dep in step.dependencies:
            if dep in failed:
                return False
            if dep not in completed:
                return False
        return True
    
    def _execute_step(self, step: PlanStep, context: Dict[str, Any]) -> Tuple[bool, Any, Optional[str]]:
        """
        Execute a single plan step.
        
        Returns: (success, result, error)
        """
        try:
            # Simulate step execution based on action type
            if step.action_type == 'search':
                result = f"Search results for: {step.parameters.get('query')}"
                return True, result, None
            
            elif step.action_type == 'analyze':
                result = "Analysis completed"
                return True, result, None
            
            elif step.action_type == 'execute':
                result = "Action executed successfully"
                return True, result, None
            
            elif step.action_type == 'verify':
                result = "Verification passed"
                return True, result, None
            
            else:
                return False, None, f"Unknown action type: {step.action_type}"
        
        except Exception as e:
            return False, None, str(e)
    
    def _should_abort_plan(self, failed_step: PlanStep, plan: Plan) -> bool:
        """Decide whether to abort the entire plan after a step failure."""
        # Abort if a critical step fails (steps with many dependents)
        dependents = sum(1 for s in plan.steps if failed_step.step_id in s.dependencies)
        
        # If more than 2 steps depend on this one, it's critical
        return dependents > 2


class HybridStrategy:
    """
    Hybrid strategy that combines ReAct and Plan-and-Execute.
    
    Uses Plan-and-Execute for well-defined tasks and ReAct for exploration.
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.react = ReActStrategy(agent_id)
        self.plan_execute = PlanAndExecuteStrategy(agent_id)
    
    def execute(self, goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute using the most appropriate strategy.
        
        Decision factors:
        - Goal clarity (clear → Plan-Execute, vague → ReAct)
        - Task complexity (simple → ReAct, complex → Plan-Execute)
        - Available information (complete → Plan-Execute, incomplete → ReAct)
        """
        strategy = self._choose_strategy(goal, context)
        
        logger.info(f"[Hybrid] Using {strategy} strategy for goal: {goal}")
        
        if strategy == 'plan-execute':
            return self.plan_execute.execute(goal, context)
        else:
            return self.react.execute(goal, context)
    
    def _choose_strategy(self, goal: str, context: Dict[str, Any]) -> str:
        """Choose the most appropriate strategy."""
        # Simple heuristics for strategy selection
        
        # If goal is very specific and we have complete information, use Plan-Execute
        if self._is_goal_specific(goal) and self._has_complete_info(context):
            return 'plan-execute'
        
        # If goal is exploratory or information is incomplete, use ReAct
        if self._is_exploratory(goal) or not self._has_complete_info(context):
            return 'react'
        
        # Default to Plan-Execute for structured tasks
        return 'plan-execute'
    
    def _is_goal_specific(self, goal: str) -> bool:
        """Check if the goal is specific and well-defined."""
        specific_keywords = ['create', 'generate', 'build', 'calculate', 'process']
        return any(keyword in goal.lower() for keyword in specific_keywords)
    
    def _is_exploratory(self, goal: str) -> bool:
        """Check if the goal is exploratory."""
        exploratory_keywords = ['explore', 'investigate', 'research', 'discover', 'find out']
        return any(keyword in goal.lower() for keyword in exploratory_keywords)
    
    def _has_complete_info(self, context: Dict[str, Any]) -> bool:
        """Check if we have complete information to plan."""
        # Simple heuristic: check if context has key information
        required_keys = ['data', 'resources', 'constraints']
        return sum(1 for key in required_keys if key in context) >= 2

# Made with Bob
