#!/usr/bin/env python3
"""
Demonstration of the Semantic-Driven Agent System.

This script shows how to use:
- Initiative Score calculation
- Semantic Loop execution
- ReAct and Plan-and-Execute strategies
- Reflexion mechanism
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from koii_os.agents.semantic_agent import (
    SemanticAgent,
    InitiativeLevel,
    InitiativeScoreCalculator
)
from koii_os.agents.strategies import (
    ReActStrategy,
    PlanAndExecuteStrategy,
    HybridStrategy
)


def demo_initiative_score():
    """Demonstrate Initiative Score calculation."""
    print("=" * 60)
    print("DEMO 1: Initiative Score Calculation")
    print("=" * 60)
    
    calculator = InitiativeScoreCalculator()
    
    # Example 1: High-performing agent
    metrics_high = {
        'tasks_completed': 95,
        'tasks_failed': 5,
        'avg_response_time': 1.2,
        'proactive_actions_count': 30,
        'user_feedback_score': 4.5,
        'total_actions': 100
    }
    
    score_high = calculator.calculate(metrics_high)
    print(f"\n📊 High-performing agent:")
    print(f"   Success rate: 95%")
    print(f"   Avg response: 1.2s")
    print(f"   Proactive ratio: 30%")
    print(f"   User satisfaction: 4.5/5")
    print(f"   → Initiative Score: {score_high:.3f}")
    
    # Example 2: Average agent
    metrics_avg = {
        'tasks_completed': 70,
        'tasks_failed': 30,
        'avg_response_time': 3.5,
        'proactive_actions_count': 15,
        'user_feedback_score': 3.0,
        'total_actions': 100
    }
    
    score_avg = calculator.calculate(metrics_avg)
    print(f"\n📊 Average agent:")
    print(f"   Success rate: 70%")
    print(f"   Avg response: 3.5s")
    print(f"   Proactive ratio: 15%")
    print(f"   User satisfaction: 3.0/5")
    print(f"   → Initiative Score: {score_avg:.3f}")
    
    # Example 3: Context adjustment
    context = {
        'system_load': 0.9,
        'user_active': False
    }
    
    adjusted = calculator.adjust_for_context(score_high, context)
    print(f"\n🔧 Context adjustment:")
    print(f"   Base score: {score_high:.3f}")
    print(f"   System load: 90% (high)")
    print(f"   User active: No")
    print(f"   → Adjusted score: {adjusted:.3f}")


def demo_semantic_loop():
    """Demonstrate Semantic Loop execution."""
    print("\n" + "=" * 60)
    print("DEMO 2: Semantic Loop (Thought → Initiative → Response)")
    print("=" * 60)
    
    agent = SemanticAgent("demo-agent-1", InitiativeLevel.MEDIUM)
    
    # Scenario 1: User needs help
    context1 = {
        'situation': 'User is working on a document',
        'user_intent': 'needs formatting help',
        'user_active': True,
        'system_load': 0.3
    }
    
    print(f"\n📝 Scenario: {context1['situation']}")
    print(f"   User intent: {context1['user_intent']}")
    print(f"   Initiative score: {agent.current_initiative_score:.3f}")
    
    action = agent.process_context(context1)
    
    if action:
        print(f"\n✅ Agent took initiative!")
        print(f"   Action: {action.action_type}")
        print(f"   Reasoning: {action.reasoning}")
        print(f"   Expected: {action.expected_outcome}")
        
        # Simulate action result
        result = "Formatting suggestions provided"
        agent.process_action_result(action, result)
        print(f"   Result: {result}")
    else:
        print(f"\n⏸️  Agent decided not to take initiative")
    
    # Scenario 2: System is busy
    context2 = {
        'situation': 'Background task running',
        'user_intent': 'unclear',
        'user_active': False,
        'system_load': 0.95
    }
    
    print(f"\n📝 Scenario: {context2['situation']}")
    print(f"   System load: 95% (very high)")
    
    action = agent.process_context(context2)
    
    if action:
        print(f"\n✅ Agent took initiative despite high load")
    else:
        print(f"\n⏸️  Agent wisely held back due to high system load")
    
    # Show agent status
    status = agent.get_status()
    print(f"\n📊 Agent Status:")
    print(f"   State: {status['state']}")
    print(f"   Initiative: {status['initiative_score']:.3f}")
    print(f"   Thoughts: {status['thought_count']}")
    print(f"   Actions: {status['action_count']}")


def demo_react_strategy():
    """Demonstrate ReAct (Reasoning + Acting) strategy."""
    print("\n" + "=" * 60)
    print("DEMO 3: ReAct Strategy (Reasoning + Acting)")
    print("=" * 60)
    
    strategy = ReActStrategy("demo-agent-2", max_steps=5)
    
    goal = "Research and summarize information about AI agents"
    context = {
        'available_tools': ['search', 'analyze', 'summarize'],
        'data': {}
    }
    
    print(f"\n🎯 Goal: {goal}")
    print(f"   Max steps: 5")
    print(f"\n🔄 Executing ReAct loop...\n")
    
    result = strategy.execute(goal, context)
    
    print(f"\n📋 Execution trace:")
    for step in result['steps']:
        print(f"\n   Step {step.step_number}:")
        print(f"   💭 Thought: {step.thought[:60]}...")
        print(f"   🎬 Action: {step.action}")
        print(f"   👁️  Observation: {step.observation}")
        print(f"   ✓ Success: {step.success}")
    
    print(f"\n🏁 Final result:")
    print(f"   Success: {result['success']}")
    print(f"   Steps taken: {result['steps_taken']}")
    print(f"   Final observation: {result['final_observation']}")


def demo_plan_execute_strategy():
    """Demonstrate Plan-and-Execute strategy."""
    print("\n" + "=" * 60)
    print("DEMO 4: Plan-and-Execute Strategy")
    print("=" * 60)
    
    strategy = PlanAndExecuteStrategy("demo-agent-3", allow_replanning=True)
    
    goal = "Create a comprehensive report on system performance"
    context = {
        'data': {'metrics': 'available'},
        'resources': {'cpu': 'available', 'memory': 'available'},
        'constraints': {'time_limit': '5 minutes'}
    }
    
    print(f"\n🎯 Goal: {goal}")
    print(f"   Replanning: Enabled")
    print(f"\n📋 Creating plan...\n")
    
    result = strategy.execute(goal, context)
    
    plan = result['plan']
    print(f"📝 Plan created with {len(plan.steps)} steps:")
    
    for step in plan.steps:
        status_icon = {
            'completed': '✅',
            'failed': '❌',
            'skipped': '⏭️',
            'pending': '⏸️',
            'in_progress': '🔄'
        }.get(step.status.value, '❓')
        
        print(f"\n   {status_icon} Step {step.step_id}: {step.description}")
        print(f"      Action: {step.action_type}")
        print(f"      Status: {step.status.value}")
        if step.dependencies:
            print(f"      Depends on: {', '.join(step.dependencies)}")
        if step.result:
            print(f"      Result: {step.result}")
    
    print(f"\n🏁 Execution result:")
    print(f"   Success: {result['success']}")
    print(f"   Completed: {result['completed_steps']} steps")
    print(f"   Failed: {result['failed_steps']} steps")


def demo_reflexion():
    """Demonstrate Reflexion (self-improvement) mechanism."""
    print("\n" + "=" * 60)
    print("DEMO 5: Reflexion Mechanism (Self-Improvement)")
    print("=" * 60)
    
    agent = SemanticAgent("demo-agent-4", InitiativeLevel.HIGH)
    
    # Simulate several actions with different outcomes
    scenarios = [
        {
            'context': {'task': 'search', 'query': 'AI agents'},
            'result': 'Success: Found 10 relevant articles',
            'success': True
        },
        {
            'context': {'task': 'analyze', 'data': 'incomplete'},
            'result': 'Failed: Insufficient data',
            'success': False
        },
        {
            'context': {'task': 'search', 'query': 'machine learning'},
            'result': 'Success: Found 15 relevant articles',
            'success': True
        },
        {
            'context': {'task': 'analyze', 'data': 'complete'},
            'result': 'Success: Analysis completed',
            'success': True
        }
    ]
    
    print("\n🔄 Running scenarios and learning...\n")
    
    for i, scenario in enumerate(scenarios, 1):
        action = agent.process_context(scenario['context'])
        if action:
            agent.process_action_result(action, scenario['result'])
            print(f"   Scenario {i}: {scenario['context']['task']} → "
                  f"{'✅ Success' if scenario['success'] else '❌ Failed'}")
    
    # Get reflexion insights
    insights = agent.reflexion.get_performance_insights()
    
    print(f"\n🧠 Reflexion Insights:")
    print(f"   Total reflexions: {insights['total_reflexions']}")
    print(f"   Success rate: {insights['success_rate']:.1%}")
    print(f"   Learned patterns: {insights['learned_patterns_count']}")
    
    if insights.get('failure_patterns'):
        print(f"\n   ⚠️  Failure patterns identified:")
        for pattern in insights['failure_patterns']:
            print(f"      • {pattern}")
    
    if insights.get('top_improvements'):
        print(f"\n   💡 Top improvement suggestions:")
        for improvement in insights['top_improvements']:
            print(f"      • {improvement}")
    
    # Show how reflexion improves future actions
    print(f"\n🎯 Applying learned lessons to new context...")
    
    new_context = {'task': 'analyze', 'data': 'incomplete'}
    enhanced = agent.reflexion.apply_reflexion(new_context)
    
    print(f"   Original context: {new_context}")
    print(f"   Enhanced with {len(enhanced.get('learned_improvements', []))} improvements")
    if enhanced.get('learned_improvements'):
        for imp in enhanced['learned_improvements']:
            print(f"      • {imp}")


def demo_hybrid_strategy():
    """Demonstrate Hybrid strategy (ReAct + Plan-Execute)."""
    print("\n" + "=" * 60)
    print("DEMO 6: Hybrid Strategy (Intelligent Selection)")
    print("=" * 60)
    
    strategy = HybridStrategy("demo-agent-5")
    
    # Scenario 1: Well-defined task → Plan-Execute
    goal1 = "Create a detailed project report"
    context1 = {
        'data': {'project_info': 'complete'},
        'resources': {'templates': 'available'},
        'constraints': {'deadline': 'tomorrow'}
    }
    
    print(f"\n📝 Scenario 1: Well-defined task")
    print(f"   Goal: {goal1}")
    print(f"   Context: Complete information available")
    
    result1 = strategy.execute(goal1, context1)
    print(f"   → Strategy selected: Plan-and-Execute")
    print(f"   → Result: {'✅ Success' if result1['success'] else '❌ Failed'}")
    
    # Scenario 2: Exploratory task → ReAct
    goal2 = "Explore and discover new optimization opportunities"
    context2 = {
        'available_tools': ['search', 'analyze']
    }
    
    print(f"\n🔍 Scenario 2: Exploratory task")
    print(f"   Goal: {goal2}")
    print(f"   Context: Limited information, exploration needed")
    
    result2 = strategy.execute(goal2, context2)
    print(f"   → Strategy selected: ReAct")
    print(f"   → Result: {'✅ Success' if result2['success'] else '❌ Failed'}")


def main():
    """Run all demonstrations."""
    print("\n" + "🤖" * 30)
    print("SEMANTIC-DRIVEN AGENT SYSTEM DEMONSTRATION")
    print("🤖" * 30)
    
    try:
        demo_initiative_score()
        time.sleep(1)
        
        demo_semantic_loop()
        time.sleep(1)
        
        demo_react_strategy()
        time.sleep(1)
        
        demo_plan_execute_strategy()
        time.sleep(1)
        
        demo_reflexion()
        time.sleep(1)
        
        demo_hybrid_strategy()
        
        print("\n" + "=" * 60)
        print("✅ All demonstrations completed successfully!")
        print("=" * 60)
        print("\nKey Takeaways:")
        print("  • Initiative Score adapts to agent performance and context")
        print("  • Semantic Loop enables proactive, context-aware behavior")
        print("  • ReAct is flexible for exploratory tasks")
        print("  • Plan-and-Execute is efficient for structured tasks")
        print("  • Reflexion enables continuous self-improvement")
        print("  • Hybrid strategy intelligently selects the best approach")
        print("\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demonstration interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

# Made with Bob
