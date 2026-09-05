export const analyzeIntegrity = (testSession) => {
    const signals = [];
    let riskScore = 0;

    // 1. Time anomaly detection: flag speeds under cognitive threshold
    const MIN_HUMAN_TIME_PER_QUESTION_MS = 4000;
    const fastAnswers = testSession.interactions.filter(i => i.timeTaken < MIN_HUMAN_TIME_PER_QUESTION_MS);

    // If > 50% of questions were answered unnaturally fast
    if (fastAnswers.length > testSession.interactions.length * 0.5) {
        signals.push({
            type: "time_anomaly",
            severity: "high",
            details: "Completion speed exceeds cognitive verification threshold."
        });
        riskScore += 0.4;
    } else if (testSession.totalTime < (testSession.interactions.length * 5000)) {
        // Entire test too fast
        signals.push({
            type: "time_anomaly",
            severity: "low",
            details: "Overall velocity suggests skimming."
        });
        riskScore += 0.15;
    }

    // 2. Pattern detection: flag identical consecutive selections
    const answers = testSession.interactions.map(i => i.selectedOptionIndex);

    // Check for uniform distribution (All Same)
    const isUniform = answers.every(v => v === answers[0]);
    if (isUniform && answers.length > 2) {
        signals.push({
            type: "pattern_detection",
            severity: "medium",
            details: "Uniform answer selection pattern detected."
        });
        riskScore += 0.3;
    }

    // 3. Coherence check: evaluate seniority claim vs test score
    const score = testSession.score;
    const claimedLevel = testSession.level || 'Mid';

    if (claimedLevel === 'Senior' && score < 30) {
        signals.push({
            type: "coherence_mismatch",
            severity: "low",
            details: "Seniority claim diverges significantly from observed output."
        });
        riskScore += 0.1;
    }

    // Aggregate and cap risk score at 1.0
    riskScore = Math.min(riskScore, 1.0);

    return {
        riskScore: Number(riskScore.toFixed(2)),
        signals,
        timestamp: new Date().toISOString()
    };
};
