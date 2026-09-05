import { v4 as uuidv4 } from 'uuid';


export const generateSkillTest = async (jobData) => {
    const OLLAMA_URL = "/ollama-api/generate";

    // 1. CHECK CACHE (OPTIMIZATION) 
    // Create a unique key based on the requirements so we don't regenerate for the same job spec
    const cacheKey = `fhn_skill_test_v2_${jobData.role}_${jobData.level}_${jobData.skills ? jobData.skills.sort().join('-') : 'gen'}`;
    const cachedData = localStorage.getItem(cacheKey);

    if (cachedData) {
        console.log("⚡ Finding Test in Local Cache... (Skipping Generation)");
        try {
            return JSON.parse(cachedData);
        } catch (e) {
            console.warn("Corrupt cache, regenerating.");
            localStorage.removeItem(cacheKey);
        }
    }

    // 2. TRY OLLAMA (LOCAL) 
    try {
        console.log("🦙 Checking Local Agent Configuration...");

        // 2a. SMART MODEL SELECTION & CONNECTION CHECK
        let selectedModel = "llama3.1";
        try {
            const tagResponse = await fetch("/ollama-api/tags");
            if (!tagResponse.ok) throw new Error("Ollama Service Unreachable");

            const tagData = await tagResponse.json();
            const availableModels = tagData.models.map(m => m.name.split(':')[0]); // ['llama3.1', 'llama3.2']

            // Prefer Faster Models
            if (availableModels.some(m => m.includes("llama3.2"))) {
                selectedModel = "llama3.2";
                console.log("🚀 Optimization: 'llama3.2' detected! Using it for 3x speed.");
            } else if (availableModels.some(m => m.includes("qwen"))) {
                selectedModel = "qwen2.5-coder"; // Example fallback
            } else {
                console.log("ℹ️ Using standard 'llama3.1' (High Precision, Slower per Token)");
            }

        } catch (connErr) {
            throw new Error("Ollama Offline: " + connErr.message);
        }

        console.log(`🦙 Generatin Test with ${selectedModel}...`);

        // 2b. GENERATION (Long Timeout)
        // Increase timeout to 120s (2 mins) for slower CPUs running 8B model
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 120000);

        console.time("Ollama Generation Time");
        const response = await fetch(OLLAMA_URL, {
            method: 'POST',
            signal: controller.signal,
            body: JSON.stringify({
                model: selectedModel,
                prompt: getPrompt(jobData),
                stream: false,
                format: "json",
                options: {
                    temperature: 0.6,
                    num_ctx: (jobData.level || '').toLowerCase().includes('senior') ? 8192 : 4096,
                    num_predict: (jobData.level || '').toLowerCase().includes('senior') ? 3000 : 2000
                }
            })
        });
        console.timeEnd("Ollama Generation Time");

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`Ollama Generation Error: ${response.status}`);
        }

        const result = await response.json();
        console.log("✅ Generation Response Received");

        // CLEANUP
        let rawText = result.response;
        rawText = rawText.replace(/```json/g, '').replace(/```/g, '').trim();

        try {
            const parsedResult = JSON.parse(rawText);

            // SAVE TO CACHE
            localStorage.setItem(cacheKey, JSON.stringify(parsedResult));
            console.log("💾 Test Saved to Cache.");

            return parsedResult;
        } catch (parseError) {
            console.error("❌ JSON Parse Error. Raw text:", rawText);
            throw new Error("Model generated invalid JSON");
        }

    } catch (e) {
        if (e.message.includes("Ollama Offline")) {
            console.error("🔴 OLLAMA SERVICE IS DOWN.");
            throw e;
        } else if (e.name === 'AbortError') {
            console.error("⏳ OLLAMA TIMEOUT.");
            throw new Error("Timeout: Agent took too long to generate the test.");
        } else {
            console.error("⚠️ OLLAMA ERROR:", e.message);
            throw e;
        }
    }
};

// HELPER: CENTRALIZED PROMPT 
const getPrompt = (jobData) => `
Generate a technical skill test for a ${jobData.level} ${jobData.role}.
Required Skills: ${jobData.skills.join(', ')}

STRICT CONSTRAINTS:
1. EXACTLY 3 Questions.
2. PURE CODING ANALYIS - NO THEORY. 
3. EMBED CODE SNIPPETS DIRECTLY IN THE "question" STRING using Markdown.
4. OPTIONS MUST BE REAL ANSWERS (e.g., specific values, error types), NOT "Option A" or placeholders.
5. Return pure JSON.

OUTPUT SCHEMA:
{
  "test_id": "${uuidv4()}",
  "role": "${jobData.role}",
  "level": "${jobData.level}",
  "questions": [
    {
      "id": "q1",
      "question": "Analyze this code:\n\n\`\`\`javascript\nconst x = ...\n\`\`\`\n\nWhat is the output?",
      "options": ["12", "undefined", "ReferenceError", "null"],
      "correct": "ReferenceError",
      "explanation": "Because x is const..."
    }
  ],
  "scoring": { "pass_threshold": 70 }
}
`;

// HELPER: JSON SCHEMA (Unused by Ollama JSON mode usually, but kept for reference or structured output if supported)
const getJsonSchema = () => ({
    // Schema definition... (Optional to keep if we ever switch back to strict structured generation providers)
});

// HELPER: HIGH-FIDELITY MOCK 
const getMockTest = (jobData) => ({
    test_id: uuidv4(),
    role: jobData.role || "Technical Lead",
    level: "Senior",
    questions: [
        {
            id: "qc1",
            question: "Identify the bug in this asynchronous loop:\n\n```javascript\nfor (var i = 0; i < 3; i++) {\n  setTimeout(() => console.log(i), 1000);\n}\n```",
            options: ["0, 1, 2", "3, 3, 3", "Undefined", "ReferenceError"],
            correct: "3, 3, 3",
            explanation: "Because 'var' is function-scoped, the variable 'i' is shared. By the time the timeouts fire (1s later), the loop has finished and 'i' is 3 for all calls. Using 'let' fixes this via block-scoping."
        },
        {
            id: "qc2",
            question: "Which of the following React `useEffect` dependencies layout is most likely to cause an infinite loop?",
            options: [
                "useEffect(() => { ... }, [])",
                "useEffect(() => { setItems([...items, newItem]) }, [items])",
                "useEffect(() => { ... }, [props.id])",
                "useEffect(() => { ... }, [dispatch])"
            ],
            correct: "useEffect(() => { setItems([...items, newItem]) }, [items])",
            explanation: "Updating a state variable (`items`) inside an effect that also depends on that same variable (`[items]`) triggers a re-render, re-running the effect, causing an infinite loop."
        },
        {
            id: "qc3",
            question: "In a Node.js event loop, when does the `setImmediate` callback execute relative to `process.nextTick`?",
            options: [
                "Before process.nextTick",
                "After process.nextTick, in the Check phase",
                "Exactly at the same time",
                "It is random"
            ],
            correct: "After process.nextTick, in the Check phase",
            explanation: "`process.nextTick` fires immediately after the current operation completes, before the event loop continues. `setImmediate` fires in the 'Check' phase of the next event loop cycle."
        }
    ],
    scoring: { pass_threshold: 65 }
});
