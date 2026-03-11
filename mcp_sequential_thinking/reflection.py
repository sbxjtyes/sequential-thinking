"""Automatic reflection engine for reasoning quality assurance.

Analyzes the reasoning chain patterns and generates reflection prompts
to guide the LLM toward more rigorous, self-aware thinking. Aligned with
human cognition: divergent/convergent balance, logical rigor, and metacognition.
"""

from typing import List, Optional, Dict, Any
from .models import ThoughtData, ThoughtType
from .logging_conf import configure_logging

logger = configure_logging("sequential-thinking.reflection")


class ReflectionEngine:
    """Generates reflection prompts based on reasoning chain patterns.

    Monitors the sequence of thoughts and detects patterns that suggest
    the reasoning might benefit from a different cognitive approach.
    Encourages human-like thinking: divergence, convergence, critique,
    analogy, and metacognition.
    """

    # Configurable thresholds
    SAME_TYPE_STREAK_THRESHOLD = 3
    NO_CRITIQUE_THRESHOLD = 5
    CONFIDENCE_DROP_THRESHOLD = 0.3
    DIVERGENCE_WITHOUT_CONVERGENCE_THRESHOLD = 4  # Too many ideas, no selection
    CONVERGENCE_WITHOUT_DIVERGENCE_THRESHOLD = 4  # Too rigid, no exploration
    NO_METACOGNITION_THRESHOLD = 8  # Long chain without stepping back
    NO_ANALOGY_SUGGEST_THRESHOLD = 6  # Complex problem, suggest analogy

    @staticmethod
    def generate_reflection(
        current_thought: ThoughtData,
        all_thoughts: List[ThoughtData],
        lang: str = "en"
    ) -> Optional[Dict[str, Any]]:
        """Generate reflection feedback based on reasoning patterns.

        Analyzes the reasoning chain for patterns that may indicate reasoning
        weaknesses, and returns structured reflection prompts.

        Args:
            current_thought: The thought just recorded.
            all_thoughts: All thoughts in the session (including current).
            lang: Language for prompts ('en' or 'zh').

        Returns:
            Optional dict with reflection data, or None if no reflection needed.
        """
        prompts = []

        # --- Check 1: Consecutive same-type thoughts ---
        prompts.extend(
            ReflectionEngine._check_same_type_streak(all_thoughts, lang)
        )

        # --- Check 2: No critique for too long ---
        prompts.extend(
            ReflectionEngine._check_missing_critique(all_thoughts, lang)
        )

        # --- Check 3: Synthesis without verification ---
        prompts.extend(
            ReflectionEngine._check_unverified_synthesis(current_thought, all_thoughts, lang)
        )

        # --- Check 4: Significant confidence drop ---
        prompts.extend(
            ReflectionEngine._check_confidence_drop(current_thought, all_thoughts, lang)
        )

        # --- Check 5: Revision referencing non-existent thought ---
        prompts.extend(
            ReflectionEngine._check_revision_target(current_thought, all_thoughts, lang)
        )

        # --- Check 6: Divergence/convergence balance (human cognition) ---
        prompts.extend(
            ReflectionEngine._check_divergence_convergence_balance(all_thoughts, lang)
        )

        # --- Check 7: Missing metacognition ---
        prompts.extend(
            ReflectionEngine._check_missing_metacognition(all_thoughts, lang)
        )

        # --- Check 8: Suggest analogy for complex problems ---
        prompts.extend(
            ReflectionEngine._check_suggest_analogy(all_thoughts, lang)
        )

        if not prompts:
            return None

        # Build reasoning graph statistics with cognitive balance
        type_distribution = ReflectionEngine._get_type_distribution(all_thoughts)
        cognitive_balance = ReflectionEngine._get_cognitive_balance(all_thoughts)

        return {
            "hasReflection": True,
            "reflectionPrompts": prompts,
            "reasoningHealth": {
                "typeDistribution": type_distribution,
                "cognitiveBalance": cognitive_balance,
                "totalThoughts": len(all_thoughts),
                "branchCount": len(set(
                    t.branch_label for t in all_thoughts if t.branch_label
                )),
                "revisionCount": len([
                    t for t in all_thoughts if t.revises_thought_id
                ]),
                "maxDepth": ReflectionEngine._calculate_max_depth(all_thoughts),
            }
        }

    @staticmethod
    def _check_same_type_streak(
        all_thoughts: List[ThoughtData], lang: str
    ) -> List[str]:
        """Detect consecutive thoughts of the same cognitive type."""
        threshold = ReflectionEngine.SAME_TYPE_STREAK_THRESHOLD
        if len(all_thoughts) < threshold:
            return []

        recent = all_thoughts[-threshold:]
        if all(t.thought_type == recent[0].thought_type for t in recent):
            thought_type = recent[0].thought_type
            if lang == "zh":
                return [
                    f"⚠️ 你已连续进行了 {threshold} 次「{thought_type}」操作。"
                    f"人脑思考需要模式切换——考虑发散(divergence)、批判(critique)、"
                    f"验证(verification)或类比(analogy)？"
                ]
            else:
                return [
                    f"⚠️ You've performed {threshold} consecutive '{thought_type}' "
                    f"operations. Human thinking benefits from mode switching — "
                    f"consider divergence, critique, verification, or analogy?"
                ]
        return []

    @staticmethod
    def _check_missing_critique(
        all_thoughts: List[ThoughtData], lang: str
    ) -> List[str]:
        """Detect long stretches without critical reflection."""
        threshold = ReflectionEngine.NO_CRITIQUE_THRESHOLD
        non_critique_streak = 0
        for t in reversed(all_thoughts):
            if t.thought_type == ThoughtType.CRITIQUE:
                break
            non_critique_streak += 1

        if non_critique_streak >= threshold:
            if lang == "zh":
                return [
                    f"⚠️ 已经 {non_critique_streak} 个思考没有进行批判性反思。"
                    f"建议审视当前推理链是否存在隐含假设、逻辑漏洞或遗漏的视角。"
                ]
            else:
                return [
                    f"⚠️ {non_critique_streak} thoughts without critical reflection. "
                    f"Consider reviewing your reasoning chain for hidden assumptions, "
                    f"logical gaps, or overlooked perspectives."
                ]
        return []

    @staticmethod
    def _check_unverified_synthesis(
        current_thought: ThoughtData,
        all_thoughts: List[ThoughtData],
        lang: str
    ) -> List[str]:
        """Detect synthesis attempts without prior verification."""
        if current_thought.thought_type != ThoughtType.SYNTHESIS:
            return []

        hypotheses = [t for t in all_thoughts if t.thought_type == ThoughtType.HYPOTHESIS]
        verifications = [t for t in all_thoughts if t.thought_type == ThoughtType.VERIFICATION]

        if hypotheses and not verifications:
            if lang == "zh":
                return [
                    f"⚠️ 你提出了 {len(hypotheses)} 个假设但尚未验证任何一个，"
                    f"就开始综合结论。建议先对核心假设进行验证(verification)。"
                ]
            else:
                return [
                    f"⚠️ You proposed {len(hypotheses)} hypotheses but verified none "
                    f"before synthesizing. Consider verifying core hypotheses first."
                ]
        return []

    @staticmethod
    def _check_confidence_drop(
        current_thought: ThoughtData,
        all_thoughts: List[ThoughtData],
        lang: str
    ) -> List[str]:
        """Detect significant drops in confidence level."""
        threshold = ReflectionEngine.CONFIDENCE_DROP_THRESHOLD
        if len(all_thoughts) < 2:
            return []

        # Find previous thought (not the current one)
        previous_thoughts = [t for t in all_thoughts if t.id != current_thought.id]
        if not previous_thoughts:
            return []

        prev = previous_thoughts[-1]
        drop = prev.confidence_level - current_thought.confidence_level

        if drop > threshold:
            if lang == "zh":
                return [
                    f"⚠️ 置信度从 {prev.confidence_level:.1f} 显著下降至 "
                    f"{current_thought.confidence_level:.1f}（下降 {drop:.1f}）。"
                    f"什么新信息或发现导致了信心动摇？建议明确记录原因。"
                ]
            else:
                return [
                    f"⚠️ Confidence dropped significantly from {prev.confidence_level:.1f} "
                    f"to {current_thought.confidence_level:.1f} (Δ={drop:.1f}). "
                    f"What new information caused this? Consider documenting the reason."
                ]
        return []

    @staticmethod
    def _check_revision_target(
        current_thought: ThoughtData,
        all_thoughts: List[ThoughtData],
        lang: str
    ) -> List[str]:
        """Validate that revision targets exist."""
        if not current_thought.revises_thought_id:
            return []

        target_ids = {str(t.id) for t in all_thoughts}
        if current_thought.revises_thought_id not in target_ids:
            if lang == "zh":
                return [
                    f"⚠️ 本思考声明修订 ID '{current_thought.revises_thought_id}' "
                    f"的思考，但该 ID 在历史中不存在。请检查 revises_thought_id 是否正确。"
                ]
            else:
                return [
                    f"⚠️ This thought claims to revise thought ID "
                    f"'{current_thought.revises_thought_id}', but that ID was not found "
                    f"in history. Please verify the revises_thought_id."
                ]
        return []

    @staticmethod
    def _check_divergence_convergence_balance(
        all_thoughts: List[ThoughtData], lang: str
    ) -> List[str]:
        """Detect imbalance between divergent and convergent thinking."""
        if len(all_thoughts) < 4:
            return []

        recent = all_thoughts[-ReflectionEngine.DIVERGENCE_WITHOUT_CONVERGENCE_THRESHOLD:]
        divergent_count = sum(1 for t in recent if t.thought_type in ThoughtType.DIVERGENT_TYPES)
        convergent_count = sum(1 for t in recent if t.thought_type in ThoughtType.CONVERGENT_TYPES)

        # Too much divergence: many ideas, no selection
        if divergent_count >= 3 and convergent_count == 0:
            if lang == "zh":
                return [
                    "💡 发散思维已产生不少想法。建议进入收敛阶段："
                    "用 convergence 或 synthesis 做选择，或 critique 筛选优劣。"
                ]
            else:
                return [
                    "💡 You've diverged with many ideas. Consider converging: "
                    "use convergence or synthesis to select, or critique to filter."
                ]

        # Too much convergence: rigid, no exploration
        recent_conv = all_thoughts[-ReflectionEngine.CONVERGENCE_WITHOUT_DIVERGENCE_THRESHOLD:]
        no_divergent_in_recent = not any(
            t.thought_type in ThoughtType.DIVERGENT_TYPES for t in recent_conv
        )
        if no_divergent_in_recent and len(recent_conv) >= 3:
            if lang == "zh":
                return [
                    "💡 推理偏收敛，可能遗漏其他可能。建议发散："
                    "用 divergence 头脑风暴、question 质疑假设、或 analogy 换视角。"
                ]
            else:
                return [
                    "💡 Reasoning is heavily convergent. Consider diverging: "
                    "use divergence to brainstorm, question to challenge assumptions, or analogy for fresh perspective."
                ]

        return []

    @staticmethod
    def _check_missing_metacognition(
        all_thoughts: List[ThoughtData], lang: str
    ) -> List[str]:
        """Suggest metacognition when reasoning chain is long without stepping back."""
        threshold = ReflectionEngine.NO_METACOGNITION_THRESHOLD
        if len(all_thoughts) < threshold:
            return []

        recent = all_thoughts[-threshold:]
        has_metacognition = any(t.thought_type == ThoughtType.METACOGNITION for t in recent)
        if not has_metacognition:
            if lang == "zh":
                return [
                    f"🧠 已连续 {threshold} 个思考未进行元认知。"
                    "建议用 metacognition 审视：当前推理路径是否合理？有无思维盲区？"
                ]
            else:
                return [
                    f"🧠 {threshold} thoughts without metacognition. "
                    "Consider using metacognition: Is your reasoning path sound? Any blind spots?"
                ]
        return []

    @staticmethod
    def _check_suggest_analogy(
        all_thoughts: List[ThoughtData], lang: str
    ) -> List[str]:
        """Suggest analogy when problem is complex but no analogy used."""
        threshold = ReflectionEngine.NO_ANALOGY_SUGGEST_THRESHOLD
        if len(all_thoughts) < threshold:
            return []

        has_analogy = any(t.thought_type == ThoughtType.ANALOGY for t in all_thoughts)
        if not has_analogy:
            if lang == "zh":
                return [
                    "🔗 问题已较复杂，尚未使用类比思维。"
                    "尝试 analogy：这个问题类似于什么？换一个领域会怎么解决？"
                ]
            else:
                return [
                    "🔗 Problem is complex but no analogy used. "
                    "Try analogy: What is this problem similar to? How would another domain solve it?"
                ]
        return []

    @staticmethod
    def _get_cognitive_balance(thoughts: List[ThoughtData]) -> Dict[str, int]:
        """Compute divergent vs convergent thought counts for reasoning health."""
        divergent = sum(1 for t in thoughts if t.thought_type in ThoughtType.DIVERGENT_TYPES)
        convergent = sum(1 for t in thoughts if t.thought_type in ThoughtType.CONVERGENT_TYPES)
        other = len(thoughts) - divergent - convergent
        return {
            "divergentCount": divergent,
            "convergentCount": convergent,
            "otherCount": other,
        }

    @staticmethod
    def _get_type_distribution(thoughts: List[ThoughtData]) -> Dict[str, int]:
        """Count thoughts by cognitive type."""
        distribution: Dict[str, int] = {}
        for t in thoughts:
            distribution[t.thought_type] = distribution.get(t.thought_type, 0) + 1
        return distribution

    @staticmethod
    def _calculate_max_depth(thoughts: List[ThoughtData]) -> int:
        """Calculate the maximum depth of the reasoning tree."""
        if not thoughts:
            return 0

        # Build parent map
        id_to_thought = {str(t.id): t for t in thoughts}
        max_depth = 1

        for t in thoughts:
            depth = 1
            current_id = t.parent_thought_id
            visited = set()
            while current_id and current_id in id_to_thought and current_id not in visited:
                visited.add(current_id)
                depth += 1
                current_id = id_to_thought[current_id].parent_thought_id
            max_depth = max(max_depth, depth)

        return max_depth
