#!/usr/bin/env python3
"""
Test suite for enhanced SemanticAgent features.

Tests:
- Proactive self-introduction
- Direction confirmation
- Clarifying questions
- Improvement suggestions
- Discovery reporting
- Decision requests
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.koii_os.agents.semantic_agent import SemanticAgent, InitiativeLevel


class SemanticAgentTests:
    """Test suite for semantic agent features."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
    
    async def test_self_introduction(self):
        """Test proactive self-introduction."""
        print("\n👋 Test 1: Self-Introduction")
        print("-" * 50)
        
        try:
            agent = SemanticAgent("test-agent-1", InitiativeLevel.MEDIUM)
            
            # Test introduction
            intro = await agent.introduce_self({
                'environment': 'test',
                'user': 'tester'
            })
            
            assert isinstance(intro, str), "Introduction should be a string"
            assert len(intro) > 0, "Introduction should not be empty"
            assert 'KOII' in intro, "Introduction should mention KOII"
            assert 'test-agent-1' in intro, "Introduction should include agent ID"
            assert agent.introduced == True, "Agent should be marked as introduced"
            
            print("✅ PASSED: Self-introduction working")
            print(f"   - Introduction generated: {len(intro)} characters")
            print(f"   - Agent marked as introduced")
            print(f"   - Contains required elements")
            self.passed += 1
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.failed += 1
            return False
    
    async def test_direction_confirmation(self):
        """Test direction confirmation during tasks."""
        print("\n🎯 Test 2: Direction Confirmation")
        print("-" * 50)
        
        try:
            agent = SemanticAgent("test-agent-2", InitiativeLevel.MEDIUM)
            
            # Test confirmation
            confirmation = await agent.confirm_direction(
                current_progress={
                    'step': 1,
                    'completed': ['Data collection', 'Initial analysis']
                },
                next_steps=[
                    'Deep analysis',
                    'Generate report',
                    'Wait for review'
                ],
                reasoning="Multiple paths available"
            )
            
            assert isinstance(confirmation, dict), "Confirmation should be a dict"
            assert 'type' in confirmation, "Missing type field"
            assert confirmation['type'] == 'direction_confirmation', "Wrong type"
            assert 'message' in confirmation, "Missing message"
            assert 'options' in confirmation, "Missing options"
            assert len(confirmation['options']) == 3, "Options count mismatch"
            assert confirmation['requires_response'] == True, "Should require response"
            
            print("✅ PASSED: Direction confirmation working")
            print(f"   - Confirmation generated")
            print(f"   - Contains {len(confirmation['options'])} options")
            print(f"   - Requires user response")
            self.passed += 1
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.failed += 1
            return False
    
    async def test_clarifying_question(self):
        """Test clarifying question asking."""
        print("\n❓ Test 3: Clarifying Questions")
        print("-" * 50)
        
        try:
            agent = SemanticAgent("test-agent-3", InitiativeLevel.MEDIUM)
            
            # Test clarifying question
            question = await agent.ask_clarifying_question(
                ambiguity="Data source is unclear",
                context={'sources': ['API', 'Database', 'File']},
                suggestions=[
                    'Use API for real-time data',
                    'Use Database for historical data',
                    'Use File for backup data'
                ]
            )
            
            assert isinstance(question, str), "Question should be a string"
            assert len(question) > 0, "Question should not be empty"
            assert 'Data source is unclear' in question, "Should mention ambiguity"
            assert len(agent.dialogue_history) > 0, "Should record in history"
            
            last_entry = agent.dialogue_history[-1]
            assert last_entry['type'] == 'clarifying_question', "Wrong history type"
            assert last_entry['requires_response'] == True, "Should require response"
            
            print("✅ PASSED: Clarifying questions working")
            print(f"   - Question generated: {len(question)} characters")
            print(f"   - Recorded in dialogue history")
            print(f"   - Requires user response")
            self.passed += 1
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.failed += 1
            return False
    
    async def test_improvement_suggestions(self):
        """Test proactive improvement suggestions."""
        print("\n💡 Test 4: Improvement Suggestions")
        print("-" * 50)
        
        try:
            agent = SemanticAgent("test-agent-4", InitiativeLevel.HIGH)
            
            # Test suggestions
            suggestions = await agent.suggest_improvements(
                current_task={'name': 'data_processing', 'status': 'in_progress'},
                improvements=[
                    {
                        'title': 'Cache frequently accessed data',
                        'description': 'Reduce API calls',
                        'benefit': '70% faster processing'
                    },
                    {
                        'title': 'Parallel processing',
                        'description': 'Process multiple items simultaneously',
                        'benefit': '3x throughput'
                    }
                ]
            )
            
            assert isinstance(suggestions, str), "Suggestions should be a string"
            assert len(suggestions) > 0, "Suggestions should not be empty"
            assert 'Cache frequently accessed data' in suggestions, "Should mention first improvement"
            assert 'Parallel processing' in suggestions, "Should mention second improvement"
            
            last_entry = agent.dialogue_history[-1]
            assert last_entry['type'] == 'improvement_suggestion', "Wrong history type"
            assert len(last_entry['improvements']) == 2, "Improvements count mismatch"
            
            print("✅ PASSED: Improvement suggestions working")
            print(f"   - Suggestions generated: {len(suggestions)} characters")
            print(f"   - Contains 2 improvements")
            print(f"   - Recorded in dialogue history")
            self.passed += 1
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.failed += 1
            return False
    
    async def test_discovery_reporting(self):
        """Test discovery reporting."""
        print("\n🔍 Test 5: Discovery Reporting")
        print("-" * 50)
        
        try:
            agent = SemanticAgent("test-agent-5", InitiativeLevel.MEDIUM)
            
            # Test discovery report
            report = await agent.report_discovery(
                finding={
                    'title': 'Unusual pattern detected',
                    'description': 'Data shows 300% increase in activity',
                    'implications': [
                        'May need to adjust capacity',
                        'Could indicate system issue',
                        'Requires immediate attention'
                    ]
                },
                importance='high'
            )
            
            assert isinstance(report, str), "Report should be a string"
            assert len(report) > 0, "Report should not be empty"
            assert 'Unusual pattern detected' in report, "Should mention finding"
            assert 'high' in report.lower() or 'HIGH' in report, "Should mention importance"
            
            last_entry = agent.dialogue_history[-1]
            assert last_entry['type'] == 'discovery_report', "Wrong history type"
            assert last_entry['importance'] == 'high', "Importance mismatch"
            
            print("✅ PASSED: Discovery reporting working")
            print(f"   - Report generated: {len(report)} characters")
            print(f"   - Importance level: high")
            print(f"   - Contains 3 implications")
            self.passed += 1
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.failed += 1
            return False
    
    async def test_decision_request(self):
        """Test decision request at critical points."""
        print("\n🔀 Test 6: Decision Requests")
        print("-" * 50)
        
        try:
            agent = SemanticAgent("test-agent-6", InitiativeLevel.MEDIUM)
            
            # Test decision request
            decision = await agent.request_decision(
                decision_point="Critical path selection needed",
                options=[
                    {
                        'name': 'Fast path',
                        'pros': ['Quick results', 'Low resource usage'],
                        'cons': ['Less accurate']
                    },
                    {
                        'name': 'Accurate path',
                        'pros': ['High accuracy', 'Comprehensive'],
                        'cons': ['Slower', 'More resources']
                    }
                ],
                recommendation="Fast path for initial analysis"
            )
            
            assert isinstance(decision, dict), "Decision should be a dict"
            assert 'type' in decision, "Missing type field"
            assert decision['type'] == 'decision_request', "Wrong type"
            assert 'message' in decision, "Missing message"
            assert 'options' in decision, "Missing options"
            assert len(decision['options']) == 2, "Options count mismatch"
            assert decision['requires_response'] == True, "Should require response"
            assert decision['critical'] == True, "Should be marked as critical"
            
            print("✅ PASSED: Decision requests working")
            print(f"   - Decision request generated")
            print(f"   - Contains 2 options")
            print(f"   - Marked as critical")
            print(f"   - Includes recommendation")
            self.passed += 1
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.failed += 1
            return False
    
    async def test_dialogue_history(self):
        """Test dialogue history management."""
        print("\n📜 Test 7: Dialogue History")
        print("-" * 50)
        
        try:
            agent = SemanticAgent("test-agent-7", InitiativeLevel.MEDIUM)
            
            # Generate some dialogue
            await agent.introduce_self({'user': 'tester'})
            await agent.ask_clarifying_question("Test ambiguity", {})
            await agent.report_discovery({'title': 'Test finding'}, 'low')
            
            # Test history retrieval
            history = agent.get_dialogue_history(limit=10)
            
            assert isinstance(history, list), "History should be a list"
            assert len(history) == 3, "Should have 3 entries"
            assert history[0]['type'] == 'introduction', "First should be introduction"
            assert history[1]['type'] == 'clarifying_question', "Second should be question"
            assert history[2]['type'] == 'discovery_report', "Third should be discovery"
            
            # Test history clearing
            agent.clear_dialogue_history()
            assert len(agent.dialogue_history) == 0, "History should be empty after clear"
            
            print("✅ PASSED: Dialogue history working")
            print(f"   - History recorded correctly")
            print(f"   - Retrieved 3 entries")
            print(f"   - Clear function works")
            self.passed += 1
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.failed += 1
            return False
    
    async def run_all_tests(self):
        """Run all semantic agent tests."""
        print("\n" + "=" * 60)
        print("🤖 SEMANTIC AGENT TEST SUITE")
        print("=" * 60)
        print("\nTesting enhanced SemanticAgent capabilities...")
        print("This validates: dialogue, questions, suggestions, etc.")
        
        # Run all tests
        await self.test_self_introduction()
        await self.test_direction_confirmation()
        await self.test_clarifying_question()
        await self.test_improvement_suggestions()
        await self.test_discovery_reporting()
        await self.test_decision_request()
        await self.test_dialogue_history()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {(self.passed/(self.passed+self.failed)*100):.1f}%")
        print("=" * 60)
        
        return self.failed == 0


async def main():
    """Run semantic agent tests."""
    try:
        tests = SemanticAgentTests()
        success = await tests.run_all_tests()
        
        if success:
            print("\n🎉 All semantic agent tests passed!")
            sys.exit(0)
        else:
            print("\n⚠️  Some tests failed. Review output above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob