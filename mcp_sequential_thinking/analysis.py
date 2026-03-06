from typing import List, Dict, Any
from collections import Counter
from datetime import datetime
import numpy as np
from .models import ThoughtData, ThoughtStage
from .logging_conf import configure_logging
from .advanced_analysis import AdvancedAnalyzer
from .config import config

logger = configure_logging("sequential-thinking.analysis")


class ThoughtAnalyzer:
    """Analyzer for thought data to extract insights and patterns."""

    @staticmethod
    def find_related_thoughts(current_thought: ThoughtData,
                             all_thoughts: List[ThoughtData],
                             max_results: int = 3) -> List[ThoughtData]:
        """Find thoughts related to the current thought.

        Args:
            current_thought: The current thought to find related thoughts for
            all_thoughts: All available thoughts to search through
            max_results: Maximum number of related thoughts to return

        Returns:
            List[ThoughtData]: Related thoughts, sorted by relevance
        """
        # First, find thoughts in the same stage
        same_stage = [t for t in all_thoughts
                     if t.stage == current_thought.stage and t.id != current_thought.id]

        # Then, find thoughts with similar tags
        if current_thought.tags:
            tag_matches = []
            for thought in all_thoughts:
                if thought.id == current_thought.id:
                    continue

                # Count matching tags
                matching_tags = set(current_thought.tags) & set(thought.tags)
                if matching_tags:
                    tag_matches.append((thought, len(matching_tags)))

            # Sort by number of matching tags (descending)
            tag_matches.sort(key=lambda x: x[1], reverse=True)
            tag_related = [t[0] for t in tag_matches]
        else:
            tag_related = []

        # Combine and deduplicate results
        combined = []
        seen_ids = set()

        # First add same stage thoughts
        for thought in same_stage:
            if thought.id not in seen_ids:
                combined.append(thought)
                seen_ids.add(thought.id)

                if len(combined) >= max_results:
                    break

        # Then add tag-related thoughts
        if len(combined) < max_results:
            for thought in tag_related:
                if thought.id not in seen_ids:
                    combined.append(thought)
                    seen_ids.add(thought.id)

                    if len(combined) >= max_results:
                        break

        return combined

    @staticmethod
    def generate_summary(thoughts: List[ThoughtData]) -> Dict[str, Any]:
        """Generate a summary of the thinking process.

        Args:
            thoughts: List of thoughts to summarize

        Returns:
            Dict[str, Any]: Summary data
        """
        if not thoughts:
            return {"summary": "No thoughts recorded yet"}

        # Group thoughts by stage
        stages = {}
        for thought in thoughts:
            if thought.stage.value not in stages:
                stages[thought.stage.value] = []
            stages[thought.stage.value].append(thought)

        # Count tags - using a more readable approach with explicit steps
        # Collect all tags from all thoughts
        all_tags = []
        for thought in thoughts:
            all_tags.extend(thought.tags)

        # Count occurrences of each tag
        tag_counts = Counter(all_tags)
        
        # Get the 5 most common tags
        top_tags = tag_counts.most_common(5)

        # Create summary
        try:
            # Safely calculate max total thoughts to avoid division by zero
            max_total = 0
            if thoughts:
                max_total = max((t.total_thoughts for t in thoughts), default=0)

            # Calculate percent complete safely
            percent_complete = 0
            if max_total > 0:
                percent_complete = (len(thoughts) / max_total) * 100

            logger.debug(f"Calculating completion: {len(thoughts)}/{max_total} = {percent_complete}%")

            # Build the summary dictionary with more readable and
            # maintainable list comprehensions
            
            # Count thoughts by stage
            stage_counts = {
                stage: len(thoughts_list) 
                for stage, thoughts_list in stages.items()
            }
            
            # Create timeline entries
            sorted_thoughts = sorted(thoughts, key=lambda x: x.thought_number)
            timeline_entries = []
            for t in sorted_thoughts:
                timeline_entries.append({
                    "number": t.thought_number,
                    "stage": t.stage.value
                })
            
            # Create top tags entries
            top_tags_entries = []
            for tag, count in top_tags:
                top_tags_entries.append({
                    "tag": tag,
                    "count": count
                })
            
            # Check if all stages are represented
            all_stages_present = all(
                stage.value in stages 
                for stage in ThoughtStage
            )
            
            # Assemble the final summary
            summary = {
                "totalThoughts": len(thoughts),
                "stages": stage_counts,
                "timeline": timeline_entries,
                "topTags": top_tags_entries,
                "completionStatus": {
                    "hasAllStages": all_stages_present,
                    "percentComplete": percent_complete
                }
            }
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            summary = {
                "totalThoughts": len(thoughts),
                "error": str(e)
            }

        return {"summary": summary}

    @staticmethod
    def _generate_contextual_prompt(thought: ThoughtData, all_thoughts: List[ThoughtData]) -> str:
        """
        Generates a contextual prompt based on the current thought and stage.
        (Private helper method)
        """
        stage = thought.stage
        content = thought.thought
        
        # Default prompt
        prompt_text = "I have just completed a thought in the '{}' stage. My last thought is: '{}'.\n\nWhat would be a logical next step?".format(stage.value, content)

        if stage == ThoughtStage.PROBLEM_DEFINITION:
            prompt_text = "I have just completed a thought in the 'Problem Definition' stage. My last thought is: '{}'.\n\nBased on this problem definition, please help me brainstorm the requirements. What key aspects should I consider? What are the potential ambiguities I need to clarify?".format(content)
        elif stage == ThoughtStage.REQUIREMENT_ANALYSIS:
            problem_thoughts = [t for t in all_thoughts if t.stage == ThoughtStage.PROBLEM_DEFINITION]
            if problem_thoughts:
                last_problem = problem_thoughts[-1].thought
                prompt_text = "I have finished defining the problem, which is: '{}'.\n\nI am now starting the 'Requirement Analysis' stage. My first thought is: '{}'.\n\nPlease help me plan the requirement analysis. What key aspects should I consider? Who are the stakeholders I should consult?".format(last_problem, content)
            else:
                 prompt_text = "I have just started the 'Requirement Analysis' stage. My first thought is: '{}'.\n\nBased on my first requirement, please help me brainstorm other related requirements.".format(content)
        elif stage == ThoughtStage.TECHNICAL_DESIGN:
            prompt_text = "I have completed the requirement analysis. My last thought on requirements is: '{}'.\n\nNow, entering the 'Technical Design' stage, please help me create a high-level technical design. What are the key components, modules, or services? What technologies would you recommend and why?".format(content)
        elif stage == ThoughtStage.IMPLEMENTATION:
            prompt_text = "The technical design is complete. My last design thought is: '{}'.\n\nI am now starting the 'Implementation' stage. Please help me break this down into smaller, manageable tasks. Can you suggest a file structure and some boilerplate code for the main components?".format(content)
        elif stage == ThoughtStage.TESTING_AND_REFACTORING:
            prompt_text = "I have finished a part of the implementation. My last thought is: '{}'.\n\nNow, in the 'Testing and Refactoring' stage, what kind of tests (unit, integration, e2e) should I write to ensure its quality? Please provide some test case ideas.".format(content)
        elif stage == ThoughtStage.INTEGRATION_AND_DEPLOYMENT:
            prompt_text = "I have finished testing and refactoring. My last thought was: '{}'.\n\nI am now entering the 'Integration and Deployment' stage. What are the next steps? Should I be thinking about documentation, environment configuration, or CI/CD pipelines?".format(content)
        
        return prompt_text

    @staticmethod
    def analyze_thought(thought: ThoughtData, all_thoughts: List[ThoughtData], lang: str = 'en', top_n: int = 3) -> Dict[str, Any]:
        """Analyze a single thought in the context of all thoughts.

        Args:
            thought: The thought to analyze
            all_thoughts: All available thoughts for context
            lang: The language of the thoughts ('en' or 'zh').
            top_n: The number of semantic recommendations to return.

        Returns:
            Dict[str, Any]: Analysis results including semantic recommendations.
        """
        # --- Existing Analysis (Tags, Stage, etc.) ---
        related_thoughts = ThoughtAnalyzer.find_related_thoughts(thought, all_thoughts)
        same_stage_thoughts = [t for t in all_thoughts if t.stage == thought.stage]
        is_first_in_stage = len(same_stage_thoughts) <= 1

        progress = (thought.thought_number / thought.total_thoughts) * 100 if thought.total_thoughts > 0 else 0

        # --- New Semantic (Content-based) Analysis (Feature Flag Enabled) ---
        semantic_recommendations = []
        if config.features.semantic_analysis.enabled and len(all_thoughts) > 1:
            try:
                logger.info(f"Performing semantic analysis for thought #{thought.thought_number} in language '{lang}'")
                similarity_matrix = AdvancedAnalyzer.calculate_similarity_matrix(all_thoughts, lang=lang)
                
                current_thought_index = -1
                for i, t in enumerate(all_thoughts):
                    if t.id == thought.id:
                        current_thought_index = i
                        break

                if current_thought_index != -1:
                    sim_scores = list(enumerate(similarity_matrix[current_thought_index]))
                    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
                    
                    for i, score in sim_scores:
                        if len(semantic_recommendations) >= top_n:
                            break
                        if all_thoughts[i].id != thought.id:
                            recommended_thought = all_thoughts[i]
                            semantic_recommendations.append({
                                "thoughtNumber": recommended_thought.thought_number,
                                "stage": recommended_thought.stage.value,
                                "snippet": recommended_thought.thought[:100] + "..." if len(recommended_thought.thought) > 100 else recommended_thought.thought,
                                "similarity": score
                            })
            except Exception as e:
                logger.error(f"Error during semantic analysis: {e}")
                pass

        # --- Combine and Return Analysis ---
        analysis_result = {
            "thoughtAnalysis": {
                "currentThought": {
                    "thoughtNumber": thought.thought_number,
                    "totalThoughts": thought.total_thoughts,
                    "nextThoughtNeeded": thought.next_thought_needed,
                    "stage": thought.stage.value,
                    "tags": thought.tags,
                    "axiomsUsed": thought.axioms_used,
                    "assumptionsChallenged": thought.assumptions_challenged,
                    "confidenceLevel": thought.confidence_level,
                    "supportingEvidence": thought.supporting_evidence,
                    "counterArguments": thought.counter_arguments,
                    "timestamp": thought.timestamp
                },
                "analysis": {
                    "relatedThoughtsCount": len(related_thoughts),
                    "relatedThoughtSummaries": [
                        {
                            "thoughtNumber": t.thought_number,
                            "stage": t.stage.value,
                            "snippet": t.thought[:100] + "..." if len(t.thought) > 100 else t.thought
                        } for t in related_thoughts
                    ],
                    "semantic_recommendations": semantic_recommendations,
                    "progress": progress,
                    "isFirstInStage": is_first_in_stage
                },
                "context": {
                    "thoughtHistoryLength": len(all_thoughts),
                    "currentStage": thought.stage.value
                }
            }
        }

        # --- Automatic Prompt Generation on New Stage Entry (Feature Flag Enabled) ---
        suggested_prompt = None
        if config.features.automatic_prompts.enabled and is_first_in_stage and thought.thought_number > 1:
            suggested_prompt = ThoughtAnalyzer._generate_contextual_prompt(thought, all_thoughts)

        analysis_result["thoughtAnalysis"]["analysis"]["suggested_prompt"] = suggested_prompt

        return analysis_result

    @staticmethod
    def get_similarity_analysis(thoughts: List[ThoughtData], threshold: float = 0.5, lang: str = 'en') -> Dict[str, Any]:
        """
        Performs a textual similarity analysis on a list of thoughts.

        Args:
            thoughts: A list of ThoughtData objects.
            threshold: The similarity threshold to consider pairs as "similar".
            lang: Language of the thoughts ('en' for English, 'zh' for Chinese).

        Returns:
            A dictionary containing the similarity analysis, including the similarity matrix
            and a list of highly similar thought pairs.
        """
        if not thoughts or len(thoughts) < 2:
            return {"message": "Not enough thoughts to perform similarity analysis."}

        similarity_matrix = AdvancedAnalyzer.calculate_similarity_matrix(thoughts, lang=lang)

        # Find pairs of thoughts with similarity above the threshold
        similar_pairs = []
        # Use numpy to find indices where similarity is above the threshold
        # We only need to check the upper triangle of the matrix (k=1)
        for i, j in zip(*np.where(similarity_matrix > threshold)):
            if i < j: # Avoid duplicate pairs and self-similarity
                pair_data = {
                    "thought_1": {
                        "thought_number": thoughts[i].thought_number,
                        "thought": thoughts[i].thought,
                    },
                    "thought_2": {
                        "thought_number": thoughts[j].thought_number,
                        "thought": thoughts[j].thought,
                    },
                    "similarity": similarity_matrix[i, j]
                }
                similar_pairs.append(pair_data)
        
        # Sort pairs by similarity score in descending order
        similar_pairs.sort(key=lambda x: x["similarity"], reverse=True)

        return {
            "similarity_analysis": {
                "similarity_matrix": similarity_matrix.tolist(),
                "similar_pairs": similar_pairs
            }
        }
