// ============================================================
// Preguntas Correctas - Cloudflare Worker Backend
// Queries 184 traditions via Workers AI and synthesizes responses
// ============================================================

const TRADITIONS = {
  abrahamic: [
    "Catholicism", "Eastern Orthodoxy", "Lutheranism", "Calvinism",
    "Anglicanism", "Methodism", "Baptist", "Pentecostalism",
    "Sunni Islam", "Shia Islam", "Sufism", "Ahmadiyya",
    "Orthodox Judaism", "Conservative Judaism", "Reform Judaism",
    "Jewish Kabbalah", "Druze", "Baha'i Faith", "Mandaeism", "Samaritanism",
    "Rastafari"
  ],
  dharmic: [
    "Advaita Vedanta", "Vishishtadvaita", "Dvaita", "Gaudiya Vaishnavism",
    "Shaivism", "Shaktism", "Smartism",
    "Theravada Buddhism", "Mahayana Buddhism", "Vajrayana Buddhism",
    "Zen Buddhism", "Pure Land Buddhism", "Nichiren Buddhism", "Tibetan Buddhism",
    "Digambara Jainism", "Shvetambara Jainism", "Sikhism", "Ayyavazhi",
    "Yoga (Patanjali)", "Samkhya", "Nyaya", "Vaisheshika", "Mimamsa"
  ],
  east_asian: [
    "Confucianism", "Neo-Confucianism", "Taoism", "Chinese Folk Religion",
    "Shinto", "Korean Shamanism", "Tenrikyo", "Seicho-no-Ie",
    "Won Buddhism", "Falun Gong", "Caodaism", "Cheondoism",
    "Yiguandao", "Omoto", "I-Kuan Tao"
  ],
  indigenous: [
    "Navajo Tradition", "Lakota Tradition", "Maya Tradition",
    "Aztec Tradition", "Inca Tradition", "Yoruba Tradition",
    "Akan Tradition", "Zulu Tradition", "Maasai Tradition",
    "San Bushmen", "Aboriginal Australian", "Maori Tradition",
    "Hawaiian Tradition", "Inuit Tradition", "Sami Tradition",
    "Celtic Tradition", "Norse Tradition", "Slavic Tradition",
    "Ancient Greek Religion", "Ancient Egyptian Religion",
    "Mesopotamian Religion", "Zoroastrianism", "Tengrism", "Bon", "Muism"
  ],
  western_philosophy: [
    "Pre-Socratics", "Platonism", "Aristotelianism", "Stoicism",
    "Epicureanism", "Skepticism", "Neoplatonism", "Scholasticism",
    "Rationalism (Descartes)", "Empiricism (Hume/Locke)", "Kantianism",
    "German Idealism (Hegel)", "Utilitarianism", "Marxism", "Pragmatism",
    "Phenomenology", "Existentialism (Sartre)", "Existentialism (Camus)",
    "Analytic Philosophy", "Logical Positivism", "Ordinary Language Philosophy",
    "Process Philosophy", "Personalism", "Critical Theory",
    "Postmodernism", "Deconstructionism", "Feminist Philosophy",
    "Philosophy of Mind", "Transhumanism", "Effective Altruism"
  ],
  modern_spiritual: [
    "Theosophy", "Anthroposophy", "Spiritism (Kardecism)",
    "New Thought", "Christian Science", "Unitarian Universalism",
    "Quakerism", "Swedenborgianism", "Scientology", "Eckankar",
    "Wicca", "Thelema", "Chaos Magick", "Neo-Paganism", "Druidry",
    "Hare Krishna (modern)", "Transcendental Meditation",
    "Osho/Rajneesh", "Gurdjieff/Fourth Way", "A Course in Miracles"
  ],
  secular: [
    "Secular Humanism", "Ethical Culture", "Atheism", "Agnosticism",
    "Deism", "Pantheism", "Panentheism", "Naturalism",
    "Scientific Materialism", "Absurdism", "Nihilism",
    "Objectivism (Rand)", "Sentientism", "Deep Ecology",
    "Cosmicism (Lovecraft)"
  ],
  african_diaspora: [
    "Vodou", "Santeria/Lukumi", "Candomble", "Umbanda",
    "Hoodoo", "Palo", "Obeah", "Kumina", "Myal", "Spiritual Baptist"
  ],
  esoteric: [
    "Hermeticism", "Gnosticism", "Rosicrucianism", "Freemasonry",
    "Kabbalah (non-Jewish)", "Sufism (universal)", "Spiritual Alchemy",
    "Hindu Tantra", "Buddhist Tantra", "Dzogchen",
    "Kashmir Shaivism", "Neo-Advaita", "Perennial Philosophy",
    "Integral Theory (Wilber)", "Metamodernism"
  ],
  contemporary: [
    "Effective Altruism (contemporary)", "Longtermism", "Digital Consciousness",
    "Simulation Theory", "Panpsychism", "Integrated Information Theory",
    "Buddhist Modernism", "Progressive Christianity", "Islamic Modernism",
    "Hindu Nationalism"
  ]
};

// Flatten all traditions into a single array
function getAllTraditions() {
  const all = [];
  for (const group of Object.values(TRADITIONS)) {
    all.push(...group);
  }
  return all;
}

// Group traditions into batches of ~10
function createBatches(traditions, batchSize = 10) {
  const batches = [];
  for (let i = 0; i < traditions.length; i += batchSize) {
    batches.push(traditions.slice(i, i + batchSize));
  }
  return batches;
}

// Simple hash for caching
async function hashQuestion(question) {
  const encoder = new TextEncoder();
  const data = encoder.encode(question.trim().toLowerCase());
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
}

// ES↔EN name equivalences for fuzzy matching
const NAME_MAP = {
  "catolicismo":"catholicism","ortodoxia cristiana":"eastern orthodoxy","luteranismo":"lutheranism",
  "calvinismo":"calvinism","anglicanismo":"anglicanism","metodismo":"methodism","bautismo":"baptist",
  "pentecostalismo":"pentecostalism","islam sunita":"sunni islam","islam chiita":"shia islam",
  "sufismo":"sufism","judaismo ortodoxo":"orthodox judaism","judaismo conservador":"conservative judaism",
  "judaismo reformista":"reform judaism","cabala judia":"jewish kabbalah","drusos":"druze",
  "fe bahai":"baha'i faith","rastafarismo":"rastafari","gaudiya vaishnavismo":"gaudiya vaishnavism",
  "shaivismo":"shaivism","shaktismo":"shaktism","smartismo":"smartism",
  "budismo theravada":"theravada buddhism","budismo mahayana":"mahayana buddhism",
  "budismo vajrayana":"vajrayana buddhism","budismo zen":"zen buddhism",
  "budismo tierra pura":"pure land buddhism","budismo nichiren":"nichiren buddhism",
  "budismo tibetano":"tibetan buddhism","jainismo digambara":"digambara jainism",
  "sijismo":"sikhism","confucianismo":"confucianism","taoismo":"taoism",
  "sintoismo":"shinto","zoroastrismo":"zoroastrianism","estoicismo":"stoicism",
  "epicureismo":"epicureanism","neoplatonismo":"neoplatonism","kantianismo":"kantianism",
  "utilitarismo":"utilitarianism","marxismo":"marxism","pragmatismo":"pragmatism",
  "fenomenologia":"phenomenology","posmodernismo":"postmodernism","transhumanismo":"transhumanism",
  "teosofia":"theosophy","ateismo":"atheism","agnosticismo":"agnosticism","nihilismo":"nihilism",
  "absurdismo":"absurdism","hermetismo":"hermeticism","gnosticismo":"gnosticism",
  "humanismo secular":"secular humanism","panteismo":"pantheism","naturalismo":"naturalism",
};
const REV_NAME_MAP = {};
for (const [es, en] of Object.entries(NAME_MAP)) { REV_NAME_MAP[en] = es; }

function namesMatch(a, b) {
  const al = a.toLowerCase().trim();
  const bl = b.toLowerCase().trim();
  if (al === bl) return true;
  if (al.includes(bl) || bl.includes(al)) return true;
  if (al.split(/\s/)[0] === bl.split(/\s/)[0]) return true;
  if (NAME_MAP[al] === bl || NAME_MAP[bl] === al) return true;
  if (REV_NAME_MAP[al] === bl || REV_NAME_MAP[bl] === al) return true;
  return false;
}

// Build the prompt for a batch of traditions
function buildBatchPrompt(question, traditions, lang, tier) {
  const list = traditions.map((t, i) => `${i + 1}. ${t}`).join("\n");
  const langInstruction = (lang === "es") ? "Respond in Spanish." : "Respond in English.";
  const isEs = (lang === "es");
  return `Question: "${question}"

Respond ONLY from these ${traditions.length} traditions:
${list}

For each tradition, write a DETAILED response of 80-120 words. ${langInstruction}

Each response MUST be substantial -- explain the tradition's core teaching on this topic, include key concepts and terminology, and cite primary sources.

FORMAT: Separate each tradition with ===TRADITION=== marker:

===TRADITION===
Name: Tradition name
Response: Detailed 150-200 word response here. This should be a full paragraph with depth, not just 1-2 sentences. Explain the philosophical reasoning, mention key texts or thinkers, and describe how this tradition uniquely approaches the question.
Source: Primary scripture or key text (e.g., Bhagavad Gita 2.20, Quran 3:185)
===TRADITION===
Name: Next tradition
Response: Another detailed 150-200 word response...
Source: Primary text

RULES:
- Each response MUST be at least 80 words.
- Only the ${traditions.length} traditions listed above
- Be PRECISE. Do not mix concepts from different traditions.
- Never attribute Christian concepts (eternal hell, original sin) to non-Christian traditions.
- Always cite the primary scripture or key thinker.
- No markdown formatting.`;
}

// Build the synthesis prompt - condensed to fit small context windows
function buildSynthesisPrompt(question, allResponses, lang) {
  const responsesText = allResponses
    .map(r => {
      const short = r.response.split(/\s+/).slice(0, 30).join(" ");
      return `- ${r.tradition}: ${short}`;
    })
    .join("\n");

  return `${allResponses.length} traditions respond to: "${question}"

${responsesText}

Write the synthesis in ENGLISH.

Use EXACTLY these headings:
SUMMARY: (1 paragraph, 100 words. NEVER start with "Across", "Throughout", "In various", or any generic opening. Instead, start with a bold claim or provocative statement. Example good starts: "Suffering is not a problem to solve but a..." / "The question of free will reveals a fundamental..." / "Every civilization has wrestled with...")
POINTS OF CONVERGENCE: (4-5 specific ideas shared across traditions. Mention tradition names naturally within the sentence. Do NOT list tradition names in parentheses at the end.)
IRRECONCILABLE TENSIONS: (3-4 fundamental disagreements. Mention traditions naturally in the text. Do NOT repeat tradition names in parentheses at the end of each point.)
MOST SURPRISING: (2-3 unexpected perspectives. Quote or paraphrase the tradition directly.)

CRITICAL FORMATTING RULES:
- Name traditions naturally WITHIN sentences, not in parentheses at the end.
- BAD: "Life is cyclical. (Hinduism, Buddhism, Jainism)"
- GOOD: "Hinduism, Buddhism, and Jainism all view life as cyclical."
- No markdown formatting, no bullet numbering.

After completing ALL FOUR sections above, add a blank line, then on SEPARATE lines suggest 4 related questions. Each line MUST start with exactly "RELATED: " followed by the question. Do NOT put these inside any of the four sections above. They go AFTER everything else.`;
}

// Call AI - tier-based provider selection
// tier: "free" | "pro"
// env: worker env bindings (OPENAI_API_KEY, AI)
async function callAI(ai, prompt, tier, env) {
  if (tier === "pro") {
    // Pro: Claude Haiku via env.CLAUDE_API_KEY
    const apiKey = env.CLAUDE_API_KEY;
    if (!apiKey) throw new Error("Claude API key not configured on server.");
    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: "claude-haiku-4-5-20251001",
        max_tokens: 4096,
        messages: [{ role: "user", content: prompt }],
      }),
    });
    const data = await response.json();
    if (data.error) {
      if (data.error.type === "insufficient_credits" || (data.error.message && data.error.message.includes("credit"))) {
        console.error("Claude credit exhausted");
        throw new Error("Pro service temporarily unavailable. Your query was not counted. Please try again later.");
      }
      throw new Error(data.error.message);
    }
    return data.content[0].text;
  }

  // tier === "free_degraded": Cloudflare AI only, no GPT fallback
  if (tier === "free_degraded") {
    try {
      const response = await ai.run("@cf/meta/llama-3.1-8b-instruct", {
        messages: [{ role: "user", content: prompt }],
        max_tokens: 2048,
        temperature: 0.7,
      });
      if (response && response.response) return response.response;
    } catch (e) {}
    throw new Error("FREE_LIMIT_REACHED");
  }

  // tier === "free": Try Cloudflare Workers AI first, fallback to GPT-4o-mini
  let cfResult = null;
  try {
    const response = await ai.run("@cf/meta/llama-3.1-8b-instruct", {
      messages: [{ role: "user", content: prompt }],
      max_tokens: 2048,
      temperature: 0.7,
    });
    if (response && response.response) cfResult = response.response;
  } catch (e) {
    // Cloudflare AI failed, will use fallback
  }

  if (cfResult) return cfResult;

  // Fallback to GPT-4o-mini
  const oaiKey = env.OPENAI_API_KEY;
  if (!oaiKey) throw new Error("Service temporarily unavailable. Please try again.");
  const oaiResponse = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${oaiKey}`,
    },
    body: JSON.stringify({
      model: "gpt-4o-mini",
      max_tokens: 2048,
      temperature: 0.7,
      messages: [{ role: "user", content: prompt }],
    }),
  });
  const oaiData = await oaiResponse.json();
  if (oaiData.error) throw new Error("Service temporarily unavailable: " + oaiData.error.message);
  return oaiData.choices[0].message.content;
}

// ============================================================
// Usage / Tier helpers
// ============================================================

// Ensure usage table exists (idempotent)
async function ensureUsageTable(db) {
  if (!db) return;
  try {
    await db.prepare(`CREATE TABLE IF NOT EXISTS usage (
      user_id TEXT PRIMARY KEY,
      tier TEXT DEFAULT 'free',
      queries_today INTEGER DEFAULT 0,
      queries_month INTEGER DEFAULT 0,
      last_reset_day TEXT,
      last_reset_month TEXT,
      pro_queries_remaining INTEGER DEFAULT 0,
      premium_queries_remaining INTEGER DEFAULT 0,
      created_at TEXT
    )`).run();
  } catch (e) {
    console.error("ensureUsageTable error:", e);
  }
}

// Get or create usage row for a user
async function getUsage(db, userId) {
  if (!db || !userId) return null;
  let row = await db.prepare("SELECT * FROM usage WHERE user_id = ?").bind(userId).first();
  if (!row) {
    const today = new Date().toISOString().slice(0, 10);
    const month = today.slice(0, 7);
    await db.prepare(
      "INSERT INTO usage (user_id, tier, queries_today, queries_month, last_reset_day, last_reset_month, pro_queries_remaining, premium_queries_remaining, created_at) VALUES (?, 'free', 0, 0, ?, ?, 0, 0, ?)"
    ).bind(userId, today, month, today).run();
    row = await db.prepare("SELECT * FROM usage WHERE user_id = ?").bind(userId).first();
  }
  // Reset daily counter if day changed
  const today = new Date().toISOString().slice(0, 10);
  if (row.last_reset_day !== today) {
    await db.prepare("UPDATE usage SET queries_today = 0, last_reset_day = ? WHERE user_id = ?").bind(today, userId).run();
    row.queries_today = 0;
    row.last_reset_day = today;
  }
  return row;
}

// Check if a user can make a query for the given tier, return {allowed, error}
function checkLimit(usage, tier) {
  if (!usage) return { allowed: true }; // no DB, allow
  if (tier === "free") {
    // First day: 10 free queries. After that: 5/day.
    const isFirstDay = usage.last_reset_day === usage.created_at;
    const dailyMax = isFirstDay ? 10 : 5;
    if (usage.queries_today >= dailyMax) {
      return { allowed: true, degraded: true, used: usage.queries_today, max: dailyMax };
    }
  } else if (tier === "pro") {
    if (usage.pro_queries_remaining <= 0) {
      return { allowed: false, error: "limit_reached", tier: "pro", used: 0, max: 0, remaining: 0 };
    }
  } else if (tier === "premium") {
    if (usage.premium_queries_remaining <= 0) {
      return { allowed: false, error: "limit_reached", tier: "premium", used: 0, max: 0, remaining: 0 };
    }
  }
  return { allowed: true };
}

// Decrement a query after successful use
async function decrementQuery(db, userId, tier) {
  if (!db || !userId) return;
  if (tier === "free") {
    await db.prepare("UPDATE usage SET queries_today = queries_today + 1 WHERE user_id = ?").bind(userId).run();
  } else if (tier === "pro") {
    await db.prepare("UPDATE usage SET pro_queries_remaining = pro_queries_remaining - 1 WHERE user_id = ?").bind(userId).run();
  } else if (tier === "premium") {
    await db.prepare("UPDATE usage SET premium_queries_remaining = premium_queries_remaining - 1 WHERE user_id = ?").bind(userId).run();
  }
}

// Parse AI response - supports both ||| format and JSON
function parseAIResponse(text) {
  if (!text) return null;

  // Try ===TRADITION=== format first (structured multi-line)
  const tradBlocks = text.split("===TRADITION===").filter(b => b.trim());
  if (tradBlocks.length > 0) {
    const results = tradBlocks.map(block => {
      const nameMatch = block.match(/Name:\s*(.+)/i);
      const responseMatch = block.match(/Response:\s*([\s\S]*?)(?=Source:|$)/i);
      const sourceMatch = block.match(/Source:\s*(.+)/i);
      if (nameMatch && responseMatch) {
        const tradition = nameMatch[1].trim().replace(/\*{1,2}/g, "").replace(/#{1,3}\s*/g, "");
        let response = responseMatch[1].trim().replace(/\*{2,}/g, "").replace(/#{1,3}\s*/g, "");
        if (sourceMatch) response += " [Source: " + sourceMatch[1].trim() + "]";
        return { tradition, response };
      }
      return null;
    }).filter(Boolean);
    if (results.length > 0) return results;
  }

  // Try ||| format (fallback for simpler models)
  const lines = text.split("\n").filter(l => l.includes("|||"));
  if (lines.length > 0) {
    return lines.map(line => {
      const parts = line.split("|||").map(p => p.trim());
      if (parts.length >= 2) {
        const tradition = parts[0].replace(/^\d+[\.\)]\s*/, "").replace(/\*{1,2}/g, "").replace(/#{1,3}\s*/g, "").trim();
        return { tradition, response: parts[1].replace(/\*{2,}/g, "") };
      }
      return null;
    }).filter(Boolean);
  }

  // Fallback: try JSON
  let cleaned = text.replace(/```json\s*/g, "").replace(/```\s*/g, "").trim();
  const arrayMatch = cleaned.match(/\[[\s\S]*\]/);
  if (arrayMatch) {
    try {
      return JSON.parse(arrayMatch[0]);
    } catch (e) {
      let fixed = arrayMatch[0].replace(/,\s*]/g, "]").replace(/'/g, '"');
      try { return JSON.parse(fixed); } catch (e2) { /* fall through */ }
    }
  }

  // Last resort: try to parse "Tradition: response" format
  const colonLines = text.split("\n").filter(l => l.includes(":") && l.trim().length > 10);
  if (colonLines.length > 0) {
    return colonLines.map(line => {
      const idx = line.indexOf(":");
      if (idx > 2 && idx < 60) {
        const tradition = line.slice(0, idx).replace(/^\d+[\.\)]\s*/, "").replace(/^[-*]\s*/, "").trim();
        const response = line.slice(idx + 1).trim();
        if (tradition && response) return { tradition, response };
      }
      return null;
    }).filter(Boolean);
  }

  return null;
}

// ============================================================
// Blog System - Question Pool & Helpers
// ============================================================

const BLOG_QUESTIONS = [
  "What is the meaning of suffering?",
  "What happens after death?",
  "Does free will exist?",
  "What is consciousness?",
  "Is there absolute truth?",
  "What is the nature of time?",
  "Why does evil exist?",
  "What is the purpose of life?",
  "What is love?",
  "What is justice?",
  "Is morality objective or subjective?",
  "What is the nature of the soul?",
  "How should we treat animals?",
  "What is enlightenment?",
  "Does God exist?",
  "What is happiness?",
  "What is wisdom?",
  "What is faith?",
  "What is the self?",
  "What is reality?",
  "Can we know anything with certainty?",
  "What is the relationship between mind and body?",
  "Is the universe eternal or created?",
  "What is the nature of beauty?",
  "What makes a life meaningful?",
  "Is violence ever justified?",
  "What is the nature of desire?",
  "How should we face death?",
  "What is forgiveness?",
  "What is the relationship between individual and community?",
  "Is there life on other worlds?",
  "What is prayer?",
  "What is the nature of evil?",
  "Can suffering lead to growth?",
  "What is the highest virtue?",
  "What is the nature of God?",
  "Is mystical experience real?",
  "What is sacred?",
  "What is the meaning of dreams?",
  "How do we know right from wrong?",
  "What is humility?",
  "Is silence a form of wisdom?",
  "What is the role of ritual in human life?",
  "Can reason and faith coexist?",
  "What is detachment?",
  "What is the nature of karma?",
  "How should we relate to nature?",
  "What is the meaning of sacrifice?",
  "Is reincarnation real?",
  "What is grace?",
  "What is the nature of truth?",
  "What is the purpose of art?",
  "What is duty?",
  "How should we raise children?",
  "What is compassion?",
  "What is the origin of the universe?",
  "Is there a universal morality?",
  "What is the relationship between power and ethics?",
  "What is hope?",
  "Can machines be conscious?",
  "What is the nature of language?",
  "What is courage?",
  "Is knowledge a burden or a gift?",
  "What is the meaning of work?",
  "What is solitude?",
  "How do we overcome fear?",
  "What is the purpose of marriage?",
  "Is war inherent to human nature?",
  "What is gratitude?",
  "What is the relationship between wealth and virtue?",
  "What is patience?",
  "How should we deal with anger?",
  "What is the nature of memory?",
  "Is progress an illusion?",
  "What is the meaning of home?",
  "What is liberation?",
  "How do we find inner peace?",
  "What is the nature of paradox?",
  "Is there meaning in chaos?",
  "What is surrender?",
  "What is the relationship between teacher and student?",
  "What is the purpose of meditation?",
  "Can we transcend the ego?",
  "What is the nature of attachment?",
  "How do we balance tradition and innovation?",
  "What is prophecy?",
  "Is celibacy a spiritual path?",
  "What is the relationship between music and the divine?",
  "What is repentance?",
  "Can the divine be named?",
  "What is the nature of miracles?",
  "How should we prepare for death?",
  "What is the relationship between body and spirit?",
  "Is ignorance a sin?",
  "What is the meaning of pilgrimage?",
  "Can darkness be a teacher?",
  "What is the purpose of community?",
  "What is the relationship between science and spirituality?",
  "Is there a soul mate?",
  "What is the nature of temptation?",
  "How do we cultivate virtue?",
  "Are moral truths objective or subjective?",
  "Are there degrees of existence?",
  "Are universals real?",
  "Are virtues universal or culturally relative?",
  "Can art change society?",
  "Can artificial consciousness be achieved?",
  "Can consciousness exist without physical substrate?",
  "Can consciousness survive bodily death?",
  "Can effects precede their causes?",
  "Can epiphenomenalism solve the interaction problem?",
  "Can materialism explain consciousness?",
  "Can mental states be reduced to physical states?",
  "Can personal identity survive death?",
  "Can punishment be justified?",
  "Can religious beliefs be rationally justified?",
  "Can rights conflict, and how do we resolve such conflicts?",
  "Can space be curved or non-Euclidean?",
  "Can time travel be logically coherent?",
  "Can virtue be taught?",
  "Can we discover moral truths through reason alone?",
  "Can we know truth with certainty?",
  "Can we survive teleportation or brain transplants?",
  "Do abstract objects exist independently?",
  "Do fictional characters exist?",
  "Do numbers exist independently of minds?",
  "Do space and time exist independently of matter?",
  "Do the ends justify the means?",
  "Do we have duties to future generations?",
  "Do we have free will?",
  "Does empty space exist?",
  "Does suffering have meaning?",
  "Does the hard problem of consciousness have a solution?",
  "Does the passage of time exist objectively?",
  "Does time have a beginning or end?",
  "Does time have a beginning?",
  "How can evil exist if God is all-good and all-powerful?",
  "How do individual things relate to universal principles?",
  "How do mental states cause physical events?",
  "How do parts relate to wholes?",
  "How do qualia relate to neural activity?",
  "How do we handle cases of multiple personality disorder?",
  "How do we judge artistic value?",
  "How do we understand mental causation in a physical world?",
  "How do we understand multiple realizability?",
  "How do we understand the concept of nothingness?",
  "How does intentionality relate to physical processes?",
  "How does mental causation work in a physical world?",
  "How should power be distributed?",
  "How should we approach moral dilemmas?",
  "Is artificial intelligence possible?",
  "Is beauty objective or subjective?",
  "Is causation reducible to correlation and temporal sequence?",
  "Is consciousness a fundamental feature of reality?",
  "Is consciousness irreducible to physical processes?",
  "Is dualism or materialism correct?",
  "Is emergence real or apparent?",
  "Is existence a property?",
  "Is functionalism about mental states correct?",
  "Is God personal or impersonal?",
  "Is government necessary?",
  "Is intention more important than action or outcome?",
  "Is mental causation possible?",
  "Is panpsychism a viable theory of mind?",
  "Is property dualism more plausible than substance dualism?",
  "Is psychological continuity necessary for identity?",
  "Is reductive physicalism viable?",
  "Is retrocausation logically possible?",
  "Is space absolute or relational?",
  "Is substance dualism true?",
  "Is the mind extended in space?",
  "Is the present moment special?",
  "Is there a distinction between numerical and qualitative identity?",
  "Is there a universal aesthetic sense?",
  "Is time linear or cyclical?",
  "Is time real or an illusion?",
  "Is truth absolute or relative?",
  "Should art be moral?",
  "Should individual interests override collective interests?",
  "What are divine attributes?",
  "What are human rights?",
  "What are individual rights and freedoms?",
  "What are our moral obligations to others?",
  "What are the arguments against God's existence?",
  "What are the arguments for God's existence?",
  "What are the challenges to religious belief?",
  "What are the fundamental categories of being?",
  "What are the implications of specific sciences?",
  "What are the limits of human knowledge?",
  "What are the major ethical theories?",
  "What are the metaphysical implications of backwards causation?",
  "What distinguishes genuine causation from mere correlation?",
  "What distinguishes material from immaterial reality?",
  "What distinguishes necessary from contingent beings?",
  "What do we owe to animals and nature?",
  "What do we owe to others?",
  "What exists?",
  "What is aesthetic experience?",
  "What is art?",
  "What is artistic value?",
  "What is beauty?",
  "What is causation?",
  "What is democracy's value?",
  "What is emergentism?",
  "What is mereological composition?",
  "What is non-reductive physicalism?",
  "What is personal identity over time?",
  "What is personal identity?",
  "What is property dualism?",
  "What is religious experience?",
  "What is scientific explanation?",
  "What is the best form of government?",
  "What is the binding problem in consciousness?",
  "What is the conceivability argument against physicalism?",
  "What is the difference between causation and mere correlation?",
  "What is the explanatory gap between mental and physical?",
  "What is the explanatory gap between physical and mental?",
  "What is the hard problem of consciousness?",
  "What is the ideal form of government?",
  "What is the knowledge argument?",
  "What is the nature of aesthetic experience?",
  "What is the nature of causation?",
  "What is the nature of consciousness?",
  "What is the nature of identity and difference?",
  "What is the nature of mental phenomena?",
  "What is the nature of mind?",
  "What is the nature of political authority?",
  "What is the nature of possibility and necessity?",
  "What is the nature of properties and relations?",
  "What is the nature of religious belief?",
  "What is the nature of religious experience?",
  "What is the nature of scientific theories?",
  "What is the nature of space?",
  "What is the nature of temporal existence?",
  "What is the nature of the divine?",
  "What is the nature of time and space?",
  "What is the nature of virtue and vice?",
  "What is the principle of sufficient reason?",
  "What is the problem of evil?",
  "What is the problem of universals?",
  "What is the proper scope of government?",
  "What is the relationship between art and society?",
  "What is the relationship between beauty and truth?",
  "What is the relationship between being and existence?",
  "What is the relationship between being and non-being?",
  "What is the relationship between brain states and mental states?",
  "What is the relationship between consciousness and identity?",
  "What is the relationship between faith and reason in religion?",
  "What is the relationship between faith and reason?",
  "What is the relationship between God and the world?",
  "What is the relationship between justice and equality?",
  "What is the relationship between mind and brain?",
  "What is the relationship between mind and matter?",
  "What is the relationship between morality and law?",
  "What is the relationship between religion and morality?",
  "What is the relationship between space and consciousness?",
  "What is the relationship between space and matter?",
  "What is the relationship between time and eternity?",
  "What is the relationship between wholes and parts?",
  "What is the role of memory in personal identity?",
  "What is the scientific method?",
  "What is the ship of Theseus problem for persons?",
  "What is the social contract?",
  "What is the source of knowledge?",
  "What is the source of moral authority?",
  "What is the source of political authority?",
  "What is the stream of consciousness?",
  "What is the unity of consciousness?",
  "What makes a government legitimate?",
  "What makes a statement true?",
  "What makes actions right or wrong?",
  "What makes an action right or wrong?",
  "What makes one event cause another?",
  "What obligations do we have to our political community?",
  "What role does the body play in personal identity?",
  "Where do rights come from?",
];

// ============================================================
// Blog Categories & Tagging System
// ============================================================

const BLOG_CATEGORIES = {
  "metaphysics": { name: "Metaphysics & Existence", color: "#3b82f6", icon: "\u{1F52E}" },
  "ethics": { name: "Ethics & Morality", color: "#22c55e", icon: "\u2696\uFE0F" },
  "mind": { name: "Mind & Consciousness", color: "#8b5cf6", icon: "\u{1F9E0}" },
  "religion": { name: "Religion & The Divine", color: "#b8860b", icon: "\u2728" },
  "politics": { name: "Politics & Society", color: "#ef4444", icon: "\u{1F3DB}\uFE0F" },
  "art": { name: "Art & Beauty", color: "#ec4899", icon: "\u{1F3A8}" },
  "science": { name: "Science & Knowledge", color: "#6b7280", icon: "\u{1F52C}" },
  "life": { name: "Life & Death", color: "#1a1a1a", icon: "\u{1F33F}" },
  "spiritual": { name: "Spiritual Practice", color: "#f97316", icon: "\u{1F549}\uFE0F" },
  "human": { name: "Human Nature", color: "#92400e", icon: "\u{1F464}" },
};

const CATEGORY_KEYWORDS = {
  mind: ["consciousness", "mind", "brain", "mental", "qualia", "dualism", "physicalism", "cognit", "psycholog", "neural", "awareness", "intentionality", "phenomenal", "epiphenomenal", "functionalism", "binding problem", "stream of consciousness"],
  religion: ["god", "divine", "religious", "faith", "prayer", "sacred", "belief", "worship", "scripture", "revelation", "miracle", "prophecy", "heaven", "hell", "angel", "demon", "church", "mosque", "temple", "covenant"],
  ethics: ["moral", "ethic", "right", "wrong", "virtue", "justice", "duty", "ought", "obligation", "rights", "punishment", "forgive", "compassion", "gratitude", "humility", "courage", "patience", "repentance"],
  metaphysics: ["exist", "being", "reality", "time", "space", "causation", "nothingness", "universal", "particular", "substance", "property", "identity", "necessity", "possibility", "mereolog", "composition", "ontolog"],
  politics: ["government", "political", "rights", "democracy", "power", "community", "social contract", "authority", "law", "citizen", "freedom", "liberty", "state", "legitimate"],
  art: ["beauty", "art", "aesthetic", "artistic", "music"],
  science: ["science", "scientific", "knowledge", "method", "empiric", "experiment", "theory", "explanation"],
  life: ["death", "suffering", "life", "purpose", "meaning", "hope", "fear", "solitude", "home", "work", "marriage", "children", "aging"],
  spiritual: ["meditation", "enlightenment", "karma", "ritual", "detachment", "liberation", "surrender", "ego", "inner peace", "pilgrimage", "celibacy", "reincarnation", "grace", "mystic"],
};

function categorizeQuestion(question) {
  const q = question.toLowerCase();
  let bestCategory = "human";
  let bestScore = 0;
  for (const [cat, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
    let score = 0;
    for (const kw of keywords) {
      if (q.includes(kw)) score++;
    }
    if (score > bestScore) {
      bestScore = score;
      bestCategory = cat;
    }
  }
  return bestCategory;
}

function generateTags(question) {
  const q = question.toLowerCase();
  const tags = new Set();
  const allKeywords = {
    "consciousness": ["consciousness", "conscious", "awareness"],
    "free-will": ["free will"],
    "morality": ["moral", "ethic", "right and wrong"],
    "god": ["god", "divine", "deity"],
    "death": ["death", "dying", "afterlife", "after death"],
    "suffering": ["suffering", "pain", "sorrow"],
    "truth": ["truth", "true", "certainty"],
    "soul": ["soul", "spirit", "atman"],
    "beauty": ["beauty", "beautiful", "aesthetic"],
    "justice": ["justice", "just", "fairness"],
    "love": ["love", "loving"],
    "time": ["time", "temporal", "eternity"],
    "knowledge": ["knowledge", "know", "epistem"],
    "existence": ["exist", "being", "reality"],
    "mind-body": ["mind and body", "mind and brain", "mental and physical", "dualism"],
    "faith": ["faith", "belief", "believe"],
    "virtue": ["virtue", "virtuous"],
    "meaning": ["meaning", "meaningful", "purpose"],
    "evil": ["evil", "sin", "wicked"],
    "identity": ["identity", "self", "personal identity"],
    "causation": ["cause", "causation", "causal"],
    "space": ["space", "spatial"],
    "art": ["art", "artistic"],
    "politics": ["government", "political", "democracy"],
    "meditation": ["meditation", "meditat"],
    "karma": ["karma", "karmic"],
    "enlightenment": ["enlightenment", "awakening"],
    "science": ["science", "scientific"],
    "nature": ["nature", "natural world"],
    "community": ["community", "society", "social"],
    "wisdom": ["wisdom", "wise"],
    "forgiveness": ["forgiv", "forgiveness"],
    "prayer": ["prayer", "pray"],
    "ritual": ["ritual", "ceremony"],
    "liberation": ["liberation", "freedom", "liberty"],
    "desire": ["desire", "want", "craving"],
    "attachment": ["attachment", "detachment"],
    "paradox": ["paradox", "contradiction"],
    "silence": ["silence", "silent"],
    "sacrifice": ["sacrifice", "sacrific"],
  };
  for (const [tag, keywords] of Object.entries(allKeywords)) {
    for (const kw of keywords) {
      if (q.includes(kw)) { tags.add(tag); break; }
    }
  }
  if (tags.size === 0) tags.add("philosophy");
  return Array.from(tags).slice(0, 8).join(",");
}

function getReadingTime(text) {
  if (!text) return 1;
  const words = text.split(/\s+/).length;
  return Math.max(1, Math.ceil(words / 200));
}

function generateSlug(question) {
  return question
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 80);
}

// Ensure blog_posts table exists with category and tags columns
async function ensureBlogTable(db) {
  if (!db) return;
  try {
    await db.prepare(`CREATE TABLE IF NOT EXISTS blog_posts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      slug TEXT UNIQUE NOT NULL,
      title TEXT NOT NULL,
      question TEXT NOT NULL,
      synthesis TEXT NOT NULL,
      traditions_json TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      published INTEGER DEFAULT 1,
      category TEXT,
      tags TEXT
    )`).run();
    // Migration: add columns if table already exists without them
    try { await db.prepare("ALTER TABLE blog_posts ADD COLUMN category TEXT").run(); } catch (e) { /* already exists */ }
    try { await db.prepare("ALTER TABLE blog_posts ADD COLUMN tags TEXT").run(); } catch (e) { /* already exists */ }
  } catch (e) {
    console.error("ensureBlogTable error:", e);
  }
}

// ============================================================
// Blog HTML Templates
// ============================================================

function blogBaseCSS() {
  return `
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: Georgia, 'Times New Roman', serif;
      background: #faf8f5;
      color: #2c2416;
      line-height: 1.7;
    }
    a { color: #8b5e3c; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .header {
      background: linear-gradient(135deg, #2c2416 0%, #4a3728 100%);
      padding: 1.2rem 2rem;
      text-align: center;
    }
    .header-inner { max-width: 800px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; }
    .header a {
      color: #e8d5b7;
      font-size: 1.4rem;
      font-weight: bold;
      letter-spacing: 0.05em;
    }
    .header a:hover { text-decoration: none; color: #fff; }
    .header-nav a { font-size: 0.95rem; margin-left: 1.5rem; color: #c4a882; }
    .header-nav a:hover { color: #fff; }
    .container { max-width: 800px; margin: 0 auto; padding: 2rem 1.5rem; }
    .footer {
      text-align: center;
      padding: 2rem;
      color: #8b7d6b;
      font-size: 0.9rem;
      border-top: 1px solid #e0d5c7;
      margin-top: 3rem;
    }
    .cta-button {
      display: inline-block;
      background: linear-gradient(135deg, #8b5e3c, #6b4226);
      color: #fff;
      padding: 0.8rem 2rem;
      border-radius: 6px;
      font-family: Georgia, serif;
      font-size: 1rem;
      margin: 1.5rem 0;
      transition: transform 0.2s;
    }
    .cta-button:hover { transform: translateY(-2px); text-decoration: none; color: #fff; }
    .category-badge {
      display: inline-block;
      padding: 0.2rem 0.7rem;
      border-radius: 999px;
      font-size: 0.8rem;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      font-weight: 600;
      color: #fff;
      text-decoration: none;
      letter-spacing: 0.02em;
    }
    .category-badge:hover { opacity: 0.85; text-decoration: none; color: #fff; }
    .tag-pill {
      display: inline-block;
      padding: 0.15rem 0.6rem;
      border-radius: 999px;
      font-size: 0.75rem;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      background: #f0e8dc;
      color: #6b4226;
      margin: 0.15rem;
      text-decoration: none;
      border: 1px solid #e0d5c7;
    }
    .tag-pill:hover { background: #e0d5c7; text-decoration: none; }
    .reading-time {
      font-size: 0.85rem;
      color: #8b7d6b;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }
  `;
}

function blogListHTML(posts, activeCategory, activeTag) {
  // Count posts per category
  const categoryCounts = {};
  for (const p of posts) {
    const cat = p.category || "human";
    categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
  }

  // Filter posts
  let filtered = posts;
  if (activeCategory) {
    filtered = posts.filter(p => (p.category || "human") === activeCategory);
  }
  if (activeTag) {
    filtered = filtered.filter(p => {
      const tags = (p.tags || "").split(",").map(t => t.trim());
      return tags.includes(activeTag);
    });
  }

  // Category pills
  const categoryPillsHTML = `
    <div class="category-filters">
      <a href="/blog" class="filter-pill ${!activeCategory ? 'active' : ''}">All (${posts.length})</a>
      ${Object.entries(BLOG_CATEGORIES).map(([key, cat]) => {
        const count = categoryCounts[key] || 0;
        if (count === 0) return "";
        return `<a href="/blog?category=${key}" class="filter-pill ${activeCategory === key ? 'active' : ''}" style="--pill-color: ${cat.color}">${cat.icon} ${cat.name} (${count})</a>`;
      }).join("")}
    </div>
  `;

  const postCards = filtered.map(p => {
    const excerpt = (p.synthesis || "").replace(/SUMMARY:\s*/i, "").slice(0, 200) + "...";
    const date = p.created_at ? p.created_at.slice(0, 10) : "";
    const cat = BLOG_CATEGORIES[p.category || "human"] || BLOG_CATEGORIES["human"];
    const readTime = getReadingTime(p.synthesis);
    const tags = (p.tags || "").split(",").filter(t => t.trim());
    return `
      <article class="post-card">
        ${p.image_url ? `<a href="/blog/${p.slug}"><img src="${escapeHTML(p.image_url)}" alt="${escapeHTML(p.title)}" class="post-card-img"></a>` : ""}
        <div class="post-card-meta">
          <a href="/blog?category=${p.category || 'human'}" class="category-badge" style="background:${cat.color}">${cat.icon} ${cat.name}</a>
          <span class="reading-time">${readTime} min read</span>
        </div>
        <a href="/blog/${p.slug}">
          <h2>${escapeHTML(p.title)}</h2>
        </a>
        <time>${date}</time>
        <p>${escapeHTML(excerpt)}</p>
        <div class="post-card-tags">
          ${tags.slice(0, 4).map(t => `<a href="/blog?tag=${encodeURIComponent(t.trim())}" class="tag-pill">${escapeHTML(t.trim())}</a>`).join("")}
        </div>
        <a href="/blog/${p.slug}" class="read-more">Read full exploration &rarr;</a>
      </article>
    `;
  }).join("");

  const filterLabel = activeCategory
    ? `Filtered by: ${(BLOG_CATEGORIES[activeCategory] || {}).name || activeCategory}`
    : activeTag
      ? `Filtered by tag: ${activeTag}`
      : "";

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>The Right Questions - Blog</title>
  <meta name="description" content="Philosophical questions explored through 184 wisdom traditions. Deep comparative analysis of humanity's biggest questions.">
  <meta property="og:title" content="The Right Questions - Blog">
  <meta property="og:description" content="Philosophical questions explored through 184 wisdom traditions.">
  <meta property="og:type" content="website">
  <link rel="alternate" type="application/rss+xml" title="The Right Questions RSS Feed" href="/blog/feed.xml">
  <style>
    ${blogBaseCSS()}
    .hero {
      position: relative;
      min-height: 70vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: url('https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/%22The_School_of_Athens%22_by_Raffaello_Sanzio_da_Urbino.jpg/1280px-%22The_School_of_Athens%22_by_Raffaello_Sanzio_da_Urbino.jpg') center/cover no-repeat;
      color: #fff;
    }
    .hero-overlay {
      position: absolute;
      inset: 0;
      background: linear-gradient(135deg, rgba(30,20,10,0.85), rgba(60,40,20,0.75));
    }
    .hero-content {
      position: relative;
      z-index: 1;
      text-align: center;
      max-width: 700px;
      padding: 3rem 2rem;
    }
    .hero h1 {
      font-size: 3rem;
      font-weight: 400;
      letter-spacing: 0.02em;
      margin-bottom: 0.5rem;
      color: #fff;
    }
    .hero-subtitle {
      font-size: 1.2rem;
      font-style: italic;
      color: #d4a96a;
      margin-bottom: 1.5rem;
    }
    .hero-desc {
      font-size: 1rem;
      line-height: 1.7;
      color: #ddd;
      margin-bottom: 2rem;
    }
    .hero-actions {
      display: flex;
      gap: 1rem;
      justify-content: center;
      flex-wrap: wrap;
      margin-bottom: 2rem;
    }
    .hero-btn {
      padding: 0.7rem 1.8rem;
      border-radius: 6px;
      text-decoration: none;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      font-size: 0.95rem;
      font-weight: 600;
      transition: all 0.2s;
    }
    .hero-btn.primary {
      background: #b8860b;
      color: #fff;
    }
    .hero-btn.primary:hover { background: #d4a96a; }
    .hero-btn.secondary {
      background: transparent;
      color: #d4a96a;
      border: 1px solid #d4a96a;
    }
    .hero-btn.secondary:hover { background: rgba(212,169,106,0.15); }
    .hero-stats {
      display: flex;
      gap: 0.8rem;
      justify-content: center;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      font-size: 0.85rem;
      color: #aaa;
    }
    @media (max-width: 640px) {
      .hero { min-height: 60vh; }
      .hero h1 { font-size: 2rem; }
      .hero-desc { font-size: 0.9rem; }
    }
    .post-card {
      background: #fff;
      border: 1px solid #e0d5c7;
      border-radius: 8px;
      padding: 1.5rem 2rem;
      margin-bottom: 1.5rem;
      transition: box-shadow 0.2s;
    }
    .post-card:hover { box-shadow: 0 4px 16px rgba(44,36,22,0.1); }
    .post-card-img { width: 100%; height: 200px; object-fit: cover; border-radius: 6px; margin-bottom: 1rem; }
    .post-card h2 { font-size: 1.3rem; color: #2c2416; margin-bottom: 0.3rem; }
    .post-card time { font-size: 0.85rem; color: #8b7d6b; }
    .post-card p { margin-top: 0.6rem; color: #4a3728; font-size: 0.95rem; }
    .post-card-meta { display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.6rem; flex-wrap: wrap; }
    .post-card-tags { margin-top: 0.5rem; }
    .read-more { font-size: 0.9rem; display: inline-block; margin-top: 0.5rem; }
    .page-title { text-align: center; margin-bottom: 1.5rem; }
    .page-title h1 { font-size: 2rem; color: #2c2416; }
    .page-title p { color: #8b7d6b; font-size: 1.05rem; margin-top: 0.3rem; }
    .category-filters {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      justify-content: center;
      margin-bottom: 2rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid #e0d5c7;
    }
    .filter-pill {
      display: inline-block;
      padding: 0.35rem 0.9rem;
      border-radius: 999px;
      font-size: 0.82rem;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      background: #fff;
      color: #4a3728;
      border: 1px solid #e0d5c7;
      text-decoration: none;
      transition: all 0.2s;
    }
    .filter-pill:hover { background: #f0e8dc; text-decoration: none; }
    .filter-pill.active { background: #4a3728; color: #fff; border-color: #4a3728; }
    .filter-label { text-align: center; color: #8b7d6b; font-size: 0.9rem; margin-bottom: 1rem; }
    .filter-label a { margin-left: 0.5rem; }
  </style>
</head>
<body>
  <div class="hero">
    <div class="hero-overlay"></div>
    <div class="hero-content">
      <h1>The Right Questions</h1>
      <p class="hero-subtitle">Philosophical inquiry across 184 world traditions</p>
      <p class="hero-desc">Each article explores how diverse philosophical, religious, and secular traditions — from Stoicism to Zen Buddhism, from Catholicism to Indigenous wisdom — answer humanity's deepest questions. AI-powered comparative analysis reveals where traditions converge, where they clash, and what surprises emerge.</p>
      <div class="hero-actions">
        <a href="/" class="hero-btn primary">Try the Interactive Tool</a>
        <a href="#articles" class="hero-btn secondary">Browse Articles ↓</a>
      </div>
      <div class="hero-stats">
        <span>184 Traditions</span>
        <span>·</span>
        <span>10 Categories</span>
        <span>·</span>
        <span>${posts.length} Articles</span>
      </div>
    </div>
  </div>
  <div class="header">
    <div class="header-inner">
      <a href="/blog">The Right Questions</a>
      <nav class="header-nav">
        <a href="/">Interactive Tool</a>
        <a href="/blog/feed.xml">RSS</a>
      </nav>
    </div>
  </div>
  <div class="container" id="articles">
    ${categoryPillsHTML}
    ${filterLabel ? '<div class="filter-label">' + escapeHTML(filterLabel) + ' <a href="/blog">Clear filter</a></div>' : ""}
    ${postCards || '<p style="text-align:center;color:#8b7d6b;">New articles published daily. Check back soon.</p>'}
  </div>
  <div class="footer">
    <p>Each article synthesizes perspectives from 184 world traditions using AI-powered comparative analysis.</p>
    <a href="/" class="cta-button">Ask Your Own Question</a>
    <p style="margin-top:1rem;">&copy; ${new Date().getFullYear()} The Right Questions · <a href="/blog/feed.xml" style="color:#b8860b;">RSS Feed</a></p>
  </div>
</body>
</html>`;
}

function blogPostHTML(post, relatedPosts, prevPost, nextPost) {
  const date = post.created_at ? post.created_at.slice(0, 10) : "";
  const excerpt = (post.synthesis || "").replace(/SUMMARY:\s*/i, "").slice(0, 160);
  const cat = BLOG_CATEGORIES[post.category || "human"] || BLOG_CATEGORIES["human"];
  const catKey = post.category || "human";
  const readTime = getReadingTime(post.synthesis);
  const tags = (post.tags || "").split(",").filter(t => t.trim());

  // Parse synthesis sections
  const synthesis = post.synthesis || "";
  const sections = [];
  const sectionNames = ["SUMMARY", "POINTS OF CONVERGENCE", "IRRECONCILABLE TENSIONS", "MOST SURPRISING"];
  for (let i = 0; i < sectionNames.length; i++) {
    const start = synthesis.indexOf(sectionNames[i] + ":");
    if (start === -1) continue;
    const contentStart = start + sectionNames[i].length + 1;
    let end = synthesis.length;
    for (let j = i + 1; j < sectionNames.length; j++) {
      const nextStart = synthesis.indexOf(sectionNames[j] + ":");
      if (nextStart !== -1) { end = nextStart; break; }
    }
    const relatedStart = synthesis.indexOf("RELATED:");
    if (relatedStart !== -1 && relatedStart < end && relatedStart > contentStart) end = relatedStart;
    sections.push({ name: sectionNames[i], content: synthesis.slice(contentStart, end).trim() });
  }

  // Parse traditions first (needed for linkifying)
  let traditions = [];
  try { traditions = JSON.parse(post.traditions_json || "[]"); } catch (e) {}

  // Linkify tradition names in text
  function linkifyTraditions(html) {
    let result = html;
    const tradNames = traditions.map(t => t.tradition).filter(Boolean).sort((a, b) => b.length - a.length);
    for (const name of tradNames) {
      const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
      const regex = new RegExp(`\\b(${name.replace(/[()]/g, "\\$&")})\\b`, "gi");
      result = result.replace(regex, `<a href="#trad-${slug}" class="tradition-link" title="See ${name}'s full response">$1</a>`);
    }
    return result;
  }

  // Use essay if available, otherwise fall back to structured synthesis
  let mainContentHTML = "";
  // Essay (narrative)
  let essayContentHTML = "";
  if (post.essay && post.essay.length > 100) {
    const essayHTML = mdToHTML(post.essay);
    const linkedEssay = linkifyTraditions(essayHTML);
    essayContentHTML = `<div class="essay-content">${linkedEssay}</div>`;
  }

  // Structured sections (Summary, Convergence, Tensions, Surprising)
  const sectionsHTML = sections.map(s => {
    const heading = s.name === "SUMMARY" ? "Summary"
      : s.name === "POINTS OF CONVERGENCE" ? "Points of Convergence"
      : s.name === "IRRECONCILABLE TENSIONS" ? "Irreconcilable Tensions"
      : "Most Surprising Insights";
    const linkedContent = linkifyTraditions(mdToHTML(s.content));
    return `<div class="synthesis-section"><h2>${heading}</h2><div>${linkedContent}</div></div>`;
  }).join("");

  // Both: essay first, then structured findings
  mainContentHTML = essayContentHTML
    + (sectionsHTML ? `<h3 class="structured-heading">Structured Findings</h3>${sectionsHTML}` : "");

  const familyMap = {};
  for (const [family, members] of Object.entries(TRADITIONS)) {
    for (const t of members) {
      familyMap[t.toLowerCase()] = family;
    }
  }

  const grouped = {};
  for (const t of traditions) {
    const family = familyMap[(t.tradition || "").toLowerCase()] || "other";
    if (!grouped[family]) grouped[family] = [];
    grouped[family].push(t);
  }

  const familyLabels = {
    abrahamic: "Abrahamic Traditions",
    dharmic: "Dharmic Traditions",
    east_asian: "East Asian Traditions",
    indigenous: "Indigenous & Ancient Traditions",
    western_philosophy: "Western Philosophy",
    modern_spiritual: "Modern Spiritual Movements",
    secular: "Secular & Naturalistic",
    african_diaspora: "African Diaspora Traditions",
    esoteric: "Esoteric & Mystical",
    contemporary: "Contemporary Thought",
    other: "Other",
  };

  const traditionsHTML = Object.entries(grouped).map(([family, items]) => {
    const label = familyLabels[family] || family;
    const itemsHTML = items.map(t =>
      `<div class="tradition-item" id="trad-${(t.tradition || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}">
        <strong>${escapeHTML(t.tradition || "")}</strong>
        <p>${mdToHTML(t.response || "")}</p>
      </div>`
    ).join("");
    return `<details class="tradition-family">
      <summary>${escapeHTML(label)} (${items.length})</summary>
      ${itemsHTML}
    </details>`;
  }).join("");

  // No related questions in blog posts (they have related posts instead)
  const relatedQuestionsHTML = "";

  // Related posts from same category
  const relatedPostsHTML = (relatedPosts && relatedPosts.length > 0)
    ? `<div class="related-posts-section">
        <h2>More in ${escapeHTML(cat.name)}</h2>
        <div class="related-posts-grid">
          ${relatedPosts.map(rp => `
            <a href="/blog/${rp.slug}" class="related-post-card">
              <span class="category-badge" style="background:${cat.color};font-size:0.7rem;">${cat.icon}</span>
              <span class="related-post-title">${escapeHTML(rp.title)}</span>
            </a>
          `).join("")}
        </div>
      </div>`
    : "";

  // Explore other categories
  const otherCategoriesHTML = `
    <div class="explore-categories">
      <h2>Explore Other Categories</h2>
      <div class="explore-pills">
        ${Object.entries(BLOG_CATEGORIES).filter(([k]) => k !== catKey).map(([k, c]) =>
          `<a href="/blog?category=${k}" class="category-badge" style="background:${c.color}">${c.icon} ${c.name}</a>`
        ).join(" ")}
      </div>
    </div>
  `;

  // Share buttons
  const postUrl = `https://therightquestions.org/blog/${post.slug}`;
  const shareText = encodeURIComponent(post.title + " - The Right Questions");
  const shareURL = encodeURIComponent(postUrl);
  const shareHTML = `
    <div class="share-buttons">
      <span class="share-label">Share:</span>
      <a href="https://twitter.com/intent/tweet?text=${shareText}&url=${shareURL}" target="_blank" rel="noopener" class="share-btn share-twitter" title="Share on Twitter">Twitter</a>
      <a href="https://www.linkedin.com/sharing/share-offsite/?url=${shareURL}" target="_blank" rel="noopener" class="share-btn share-linkedin" title="Share on LinkedIn">LinkedIn</a>
      <a href="mailto:?subject=${shareText}&body=${shareURL}" class="share-btn share-email" title="Share via Email">Email</a>
    </div>
  `;

  // Prev/Next navigation
  const navHTML = (prevPost || nextPost) ? `
    <nav class="post-navigation">
      ${prevPost ? `<a href="/blog/${prevPost.slug}" class="nav-prev">&larr; ${escapeHTML(prevPost.title)}</a>` : '<span></span>'}
      ${nextPost ? `<a href="/blog/${nextPost.slug}" class="nav-next">${escapeHTML(nextPost.title)} &rarr;</a>` : '<span></span>'}
    </nav>
  ` : "";

  // Tags HTML
  const tagsHTML = tags.length > 0 ? `
    <div class="post-tags">
      ${tags.map(t => `<a href="/blog?tag=${encodeURIComponent(t.trim())}" class="tag-pill">${escapeHTML(t.trim())}</a>`).join("")}
    </div>
  ` : "";

  // Schema.org structured data
  const schemaOrg = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": post.title,
    "datePublished": date,
    "description": excerpt,
    "author": { "@type": "Organization", "name": "The Right Questions" },
    "publisher": { "@type": "Organization", "name": "The Right Questions" },
    "articleSection": cat.name,
    "keywords": tags.join(", "),
  });

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHTML(post.title)} - The Right Questions</title>
  <meta name="description" content="${escapeHTML(excerpt)}">
  <meta property="og:title" content="${escapeHTML(post.title)} - The Right Questions">
  <meta property="og:description" content="${escapeHTML(excerpt)}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="${postUrl}">
  ${post.image_url ? `<meta property="og:image" content="${escapeHTML(post.image_url)}">` : ""}
  ${post.image_url ? `<meta name="twitter:card" content="summary_large_image">` : ""}
  ${post.image_url ? `<meta name="twitter:image" content="${escapeHTML(post.image_url)}">` : ""}
  <meta property="article:published_time" content="${date}">
  <meta property="article:section" content="${escapeHTML(cat.name)}">
  ${tags.map(t => `<meta property="article:tag" content="${escapeHTML(t.trim())}">`).join("\n  ")}
  <link rel="alternate" type="application/rss+xml" title="The Right Questions RSS Feed" href="/blog/feed.xml">
  <script type="application/ld+json">${schemaOrg}</script>
  <style>
    ${blogBaseCSS()}
    .article-hero-img { width: 100%; max-height: 400px; object-fit: cover; border-radius: 12px; margin-bottom: 2rem; }
    .essay-content { font-size: 1.05rem; line-height: 1.85; color: #2c2416; }
    .essay-content p, .essay-content br+br { margin-bottom: 1.2rem; }
    .tradition-link { color: #b8860b; text-decoration: none; border-bottom: 1px dotted #b8860b; transition: all 0.2s; }
    .tradition-link:hover { color: #8b6914; border-bottom-style: solid; background: rgba(184,134,11,0.06); }
    .structured-heading { font-size: 1.2rem; color: #4a3728; margin: 2.5rem 0 1.2rem; padding-top: 1.5rem; border-top: 1px solid #e0d5c7; }
    .tradition-item { scroll-margin-top: 80px; }
    .article-header { text-align: center; margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 1px solid #e0d5c7; }
    .article-header h1 { font-size: 2rem; color: #2c2416; line-height: 1.3; margin-bottom: 0.5rem; }
    .article-meta { display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-top: 0.6rem; }
    .article-meta time { color: #8b7d6b; font-size: 0.95rem; }
    .synthesis-section { margin-bottom: 2rem; }
    .synthesis-section h2 {
      font-size: 1.25rem;
      color: #6b4226;
      margin-bottom: 0.6rem;
      padding-bottom: 0.3rem;
      border-bottom: 2px solid #e8d5b7;
    }
    .synthesis-section p { color: #3a2e1e; white-space: pre-line; }
    .traditions-heading {
      font-size: 1.4rem;
      color: #2c2416;
      text-align: center;
      margin: 2.5rem 0 1rem;
      padding-top: 1.5rem;
      border-top: 1px solid #e0d5c7;
    }
    .tradition-family {
      background: #fff;
      border: 1px solid #e0d5c7;
      border-radius: 6px;
      margin-bottom: 0.8rem;
      overflow: hidden;
    }
    .tradition-family summary {
      padding: 0.8rem 1.2rem;
      cursor: pointer;
      font-weight: bold;
      color: #4a3728;
      background: #f5efe7;
    }
    .tradition-family summary:hover { background: #ede4d6; }
    .tradition-item { padding: 0.8rem 1.2rem; border-top: 1px solid #f0e8dc; }
    .tradition-item strong { color: #6b4226; }
    .tradition-item p { font-size: 0.92rem; margin-top: 0.3rem; color: #3a2e1e; }
    .cta-section { text-align: center; margin: 3rem 0 1rem; }
    .cta-section p { color: #8b7d6b; margin-bottom: 0.5rem; }
    .related-questions { margin: 2rem 0; }
    .related-questions h2 { font-size: 1.15rem; color: #6b4226; margin-bottom: 0.5rem; }
    .related-questions ul { list-style: none; padding: 0; }
    .related-questions li { padding: 0.3rem 0; color: #4a3728; }
    .related-questions li::before { content: "\\2022 "; color: #8b5e3c; }
    .post-tags { margin-top: 0.8rem; }
    .share-buttons {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      margin: 1.5rem 0;
      padding: 1rem;
      background: #f5efe7;
      border-radius: 8px;
      flex-wrap: wrap;
    }
    .share-label { font-size: 0.9rem; color: #8b7d6b; font-weight: bold; }
    .share-btn {
      display: inline-block;
      padding: 0.3rem 0.8rem;
      border-radius: 4px;
      font-size: 0.82rem;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      color: #fff;
      text-decoration: none;
    }
    .share-btn:hover { opacity: 0.85; text-decoration: none; color: #fff; }
    .share-twitter { background: #1da1f2; }
    .share-linkedin { background: #0077b5; }
    .share-email { background: #6b7280; }
    .post-navigation {
      display: flex;
      justify-content: space-between;
      gap: 1rem;
      margin: 2rem 0;
      padding: 1.5rem 0;
      border-top: 1px solid #e0d5c7;
      border-bottom: 1px solid #e0d5c7;
    }
    .post-navigation a {
      max-width: 45%;
      font-size: 0.9rem;
      color: #8b5e3c;
    }
    .nav-next { text-align: right; }
    .related-posts-section {
      margin: 2rem 0;
    }
    .related-posts-section h2 {
      font-size: 1.15rem;
      color: #6b4226;
      margin-bottom: 0.8rem;
    }
    .related-posts-grid {
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
    }
    .related-post-card {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      padding: 0.7rem 1rem;
      background: #fff;
      border: 1px solid #e0d5c7;
      border-radius: 6px;
      text-decoration: none;
      transition: box-shadow 0.2s;
    }
    .related-post-card:hover { box-shadow: 0 2px 8px rgba(44,36,22,0.08); text-decoration: none; }
    .related-post-title { color: #2c2416; font-size: 0.95rem; }
    .explore-categories {
      margin: 2rem 0;
    }
    .explore-categories h2 {
      font-size: 1.15rem;
      color: #6b4226;
      margin-bottom: 0.8rem;
    }
    .explore-pills {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }
  </style>
</head>
<body>
  <div class="header">
    <div class="header-inner">
      <a href="/">The Right Questions</a>
      <nav class="header-nav">
        <a href="/blog">Blog</a>
        <a href="/blog/feed.xml">RSS</a>
      </nav>
    </div>
  </div>
  <div class="container">
    <article>
      ${post.image_url ? `<img src="${escapeHTML(post.image_url)}" alt="${escapeHTML(post.title)}" class="article-hero-img">` : ""}
      <div class="article-header">
        <a href="/blog?category=${catKey}" class="category-badge" style="background:${cat.color}">${cat.icon} ${cat.name}</a>
        <h1>${escapeHTML(post.title)}</h1>
        <div class="article-meta">
          <time datetime="${date}">${date}</time>
          <span class="reading-time">${readTime} min read</span>
        </div>
        ${tagsHTML}
      </div>
      ${mainContentHTML}
      ${shareHTML}
      <h3 class="traditions-heading">What 184 Traditions Say</h3>
      ${traditionsHTML}
      ${relatedQuestionsHTML}
      ${relatedPostsHTML}
      ${otherCategoriesHTML}
      ${navHTML}
      <div class="cta-section">
        <p>Have your own question for the world's wisdom traditions?</p>
        <a href="/" class="cta-button">Ask Your Own Question</a>
      </div>
    </article>
  </div>
  <div class="footer">
    <a href="/blog">&larr; All Explorations</a>
    <p style="margin-top:0.5rem;">&copy; ${new Date().getFullYear()} The Right Questions</p>
  </div>
</body>
</html>`;
}

function mdToHTML(str) {
  if (!str) return "";
  return escapeHTML(str)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/#{1,3}\s+/g, "")
    .replace(/\*{2,}/g, "")
    .replace(/^\d+[\.\)]\s*/gm, "")                    // Remove numbering (1. 2. 3.)
    .replace(/\n/g, "<br>")                              // Each line on its own line
    .replace(/(<br>){3,}/g, "<br><br>")                  // Collapse excessive line breaks
    .replace(/\[Source:\s*([^\]]+)\]/g, '<span style="display:block;margin-top:6px;font-size:0.8em;color:#888;font-style:italic;">📖 $1</span>');
}

function escapeHTML(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function escapeXML(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

// Generate a varied image prompt based on category
function generateImagePrompt(title, category) {
  const styles = {
    metaphysics: {
      medium: "cosmic watercolor with ink splashes",
      palette: "deep indigo, midnight blue, silver, white",
      elements: "celestial bodies, infinite mirrors, geometric fractals, floating spheres",
      mood: "vast, mysterious, infinite",
    },
    ethics: {
      medium: "woodcut print with gold leaf accents",
      palette: "black, ivory, deep red, gold",
      elements: "balanced scales, intertwined hands, ancient scrolls, a crossroads path",
      mood: "weighty, dignified, consequential",
    },
    mind: {
      medium: "surrealist digital painting",
      palette: "electric violet, cyan, deep purple, neural white",
      elements: "neural networks, labyrinths, eyes within eyes, light emerging from darkness",
      mood: "enigmatic, layered, dreamlike",
    },
    religion: {
      medium: "Byzantine-inspired mosaic painting",
      palette: "gold, deep crimson, royal blue, ivory",
      elements: "cathedral arches, sacred geometry, light rays through stained glass, doves",
      mood: "reverent, luminous, transcendent",
    },
    politics: {
      medium: "bold social realism mural",
      palette: "earth tones, terracotta, olive green, charcoal",
      elements: "columns, crowds, agora, raised platforms, shared table",
      mood: "civic, powerful, communal",
    },
    art: {
      medium: "impressionist garden scene",
      palette: "rose, lavender, soft gold, sage green",
      elements: "flowing brushstrokes, dancing light, blossoming forms, musical waves",
      mood: "beautiful, sensory, ephemeral",
    },
    science: {
      medium: "technical illustration meets fine art",
      palette: "steel blue, copper, warm gray, white",
      elements: "lenses, prisms, constellation maps, botanical diagrams",
      mood: "precise, curious, illuminating",
    },
    life: {
      medium: "chiaroscuro oil painting",
      palette: "deep amber, burnt sienna, warm black, candlelight gold",
      elements: "hourglasses, seeds sprouting, winding rivers, doorways between light and shadow",
      mood: "contemplative, bittersweet, profound",
    },
    spiritual: {
      medium: "silk scroll painting with watercolor wash",
      palette: "saffron, deep teal, warm white, lotus pink",
      elements: "meditation posture, mountain peaks, incense smoke, still water reflections",
      mood: "serene, devotional, inward",
    },
    human: {
      medium: "Renaissance portrait study",
      palette: "warm brown, ochre, olive, cream",
      elements: "expressive faces, gesturing hands, gathered circles, hearth fire",
      mood: "intimate, warm, deeply human",
    },
  };

  const s = styles[category] || styles.human;
  return `${s.medium}. Color palette: ${s.palette}. Visual elements: ${s.elements}. The specific topic is: "${title}". Mood: ${s.mood}. No text, no words, no letters, no writing. Artistic, evocative, suitable as a philosophical journal cover illustration.`;
}

// Generate a custom image prompt using AI based on article content
async function generateSmartImagePrompt(title, synthesis, env) {
  const safeTitle = title.replace(/suffering|death|evil|violence|war|kill|anger|hate|suicide/gi, "contemplation");
  const safeSynthesis = (synthesis || "").replace(/suffering|death|evil|violence|war|kill|anger|hate|suicide|murder/gi, "contemplation").slice(0, 500);

  // Pick a deterministic but varied style based on title hash
  const ART_STYLES = [
    "Japanese ukiyo-e woodblock print with bold outlines and flat color areas",
    "charcoal and white chalk drawing on toned gray paper, dramatic contrast",
    "stained glass window design with lead lines and jewel-toned translucent colors",
    "vintage botanical scientific illustration with fine crosshatching",
    "art deco geometric poster with metallic gold and deep navy",
    "loose watercolor wash with splashes and drips, minimal and expressive",
    "Byzantine gold-ground mosaic with tessera texture",
    "paper cut-out collage using torn textured papers in earth tones",
    "chalk pastel on black paper, glowing colors emerging from darkness",
    "two-color linocut print, bold graphic shapes in rust and black",
    "ancient fresco fragment with cracked plaster texture and faded pigments",
    "Tibetan thangka painting with intricate detail and symbolic imagery",
    "Persian miniature painting with ultra-fine detail and flat perspective",
    "African mud cloth inspired pattern with geometric symbolic motifs",
    "celestial chart illustration with constellation lines and aged paper",
    "medieval illuminated manuscript initial letter with gold leaf",
    "cubist still life with fragmented geometric forms and muted palette",
    "Dutch Golden Age vanitas painting with dramatic side lighting",
    "Chinese ink wash painting with minimal brushstrokes on rice paper",
    "Australian Aboriginal dot painting with concentric circles and earth pigments",
  ];
  const styleIdx = Math.abs(safeTitle.split("").reduce((a, c) => a + c.charCodeAt(0), 0)) % ART_STYLES.length;
  const forcedStyle = ART_STYLES[styleIdx];

  const metaPrompt = `Create a DALL-E 3 image prompt for an article titled "${safeTitle}".

THE ART STYLE MUST BE: ${forcedStyle}. This is mandatory -- the entire image must look like this style.

Article excerpt: "${safeSynthesis.slice(0, 200)}"

Rules:
- The image MUST look like ${forcedStyle} -- not an oil painting, not photorealistic
- Pick ONE symbolic visual metaphor for the topic
- No text, no letters, no words, no human faces
- Abstract-symbolic, evocative

Output ONLY the prompt. Max 60 words.`;

  try {
    const resp = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": "Bearer " + env.OPENAI_API_KEY },
      body: JSON.stringify({ model: "gpt-4o-mini", max_tokens: 150, temperature: 1.0, messages: [{ role: "user", content: metaPrompt }] }),
    });
    const data = await resp.json();
    if (data.choices && data.choices[0]) {
      return data.choices[0].message.content.trim();
    }
  } catch (e) {
    console.error("Smart prompt generation failed:", e.message);
  }
  // Fallback to basic prompt
  return `Oil painting, warm earth tones. Abstract symbolic composition about "${safeTitle}". No text, no faces. Rembrandt lighting. Philosophical journal cover.`;
}

// Generate a blog post by running the AI pipeline internally
async function generateBlogPost(question, env) {
  // Start image generation FIRST (runs in parallel with everything else)
  let imagePromise = null;
  if (env.OPENAI_API_KEY) {
    const imagePrompt = `A contemplative, scholarly oil painting in warm earth tones (amber, sienna, deep brown, gold). Style: Renaissance-meets-modern, atmospheric, slightly abstract. Subject: a symbolic visual metaphor for the philosophical question "${question}". No text, no words, no letters. Soft warm lighting from the left, aged parchment texture in background, classical composition. Mood: thoughtful, timeless, reverent. Think Rembrandt lighting with Rothko's emotional depth.`;
    imagePromise = fetch("https://api.openai.com/v1/images/generations", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": "Bearer " + env.OPENAI_API_KEY },
      body: JSON.stringify({ model: "dall-e-3", prompt: imagePrompt, n: 1, size: "1792x1024", quality: "standard" }),
    }).then(r => r.json()).then(d => (d.data && d.data[0]) ? d.data[0].url : "").catch(() => "");
  }

  const allTraditions = getAllTraditions();
  const batchSize = 40;
  const batches = createBatches(allTraditions, batchSize);
  const allResponses = [];

  // Process all batches in parallel
  const batchPromises = batches.map(async (batch) => {
    try {
      const prompt = buildBatchPrompt(question, batch, "en", "free");
      const rawResponse = await callAI(env.AI, prompt, "free", env);
      const parsed = parseAIResponse(rawResponse);
      if (parsed && Array.isArray(parsed) && parsed.length > 0) return parsed;
      return batch.map(t => ({ tradition: t, response: "Response not available." }));
    } catch (e) {
      return batch.map(t => ({ tradition: t, response: "Error generating response." }));
    }
  });

  const batchResults = await Promise.all(batchPromises);
  for (const results of batchResults) allResponses.push(...results);

  // Fuzzy match
  const filteredResponses = [];
  const matched = new Set();
  for (const requested of allTraditions) {
    let bestMatch = null;
    for (const r of allResponses) {
      if (!r || !r.tradition || !r.response) continue;
      if (namesMatch(requested, r.tradition) && !matched.has(r)) { bestMatch = r; break; }
    }
    if (bestMatch) {
      matched.add(bestMatch);
      filteredResponses.push({ tradition: requested, response: bestMatch.response });
    } else {
      filteredResponses.push({ tradition: requested, response: "No response available for this tradition." });
    }
  }

  // Generate synthesis (structured, for the interactive tool)
  const synthesisPrompt = buildSynthesisPrompt(question, filteredResponses, "en");
  const synthesis = await callAI(env.AI, synthesisPrompt, "free", env);

  // Generate narrative essay for the blog
  const top15 = filteredResponses
    .filter(r => r.response && !r.response.includes("not available") && !r.response.includes("Error"))
    .slice(0, 15)
    .map(r => `${r.tradition}: ${r.response.slice(0, 200)}`)
    .join("\n");

  const essayPrompt = `You are a philosophical essayist writing for an academic journal called "The Right Questions".

Question: "${question}"

Structured synthesis:
${synthesis.slice(0, 800)}

Top tradition responses:
${top15}

Write a 600-800 word essay that:
- Opens with a compelling hook (NEVER start with "Across traditions" or generic openings)
- Weaves together the most interesting responses into a flowing narrative
- Mentions specific traditions BY NAME (e.g., "Stoicism teaches that...", "In Zen Buddhism...")
- Highlights surprising convergences and tensions naturally within the text
- Quotes or paraphrases specific traditions directly
- Ends with a thought-provoking reflection that stays with the reader
- Reads like a New Yorker or Aeon essay, not a research report
- NO section headers, NO bullet points, NO numbering -- just flowing prose paragraphs
- NO markdown formatting`;

  let essay = "";
  try {
    essay = await callAI(env.AI, essayPrompt, "free", env);
  } catch (e) {
    essay = synthesis; // fallback to structured synthesis
  }

  const slug = generateSlug(question);
  const title = question;
  const category = categorizeQuestion(question);
  const tags = generateTags(question);

  // Save post
  const imageUrl = "";
  await ensureBlogTable(env.DB);
  await env.DB.prepare(
    "INSERT OR REPLACE INTO blog_posts (slug, title, question, synthesis, essay, traditions_json, created_at, published, category, tags, image_url) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), 1, ?, ?, ?)"
  ).bind(slug, title, question, synthesis, essay, JSON.stringify(filteredResponses), category, tags, imageUrl).run();

  return { slug, title, question, synthesis, essay, traditions_json: JSON.stringify(filteredResponses), category, tags, image_url: imageUrl };
}

// Main handler
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // CORS headers
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, X-User-ID, X-Blog-Key",
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    // Serve static files for Pages (/ and /es both serve index.html)
    if (url.pathname === "/" || url.pathname === "/index.html" || url.pathname === "/es" || url.pathname === "/es/") {
      if (env.ASSETS) {
        const assetUrl = new URL(request.url);
        assetUrl.pathname = "/index.html";
        return env.ASSETS.fetch(new Request(assetUrl, request));
      }
      return new Response("Static assets not configured", { status: 404 });
    }

    // API: Get traditions list
    if (url.pathname === "/api/traditions" && request.method === "GET") {
      return new Response(JSON.stringify(TRADITIONS), {
        headers: { "Content-Type": "application/json", ...corsHeaders },
      });
    }

    // ============================================================
    // Blog Routes
    // ============================================================

    // GET /blog - List all published blog posts
    if (url.pathname === "/blog" || url.pathname === "/blog/") {
      const activeCategory = url.searchParams.get("category") || "";
      const activeTag = url.searchParams.get("tag") || "";
      if (env.DB) {
        try {
          await ensureBlogTable(env.DB);
          const { results } = await env.DB.prepare(
            "SELECT slug, title, synthesis, created_at, category, tags, image_url FROM blog_posts WHERE published = 1 ORDER BY created_at DESC"
          ).all();
          return new Response(blogListHTML(results || [], activeCategory, activeTag), {
            headers: { "Content-Type": "text/html; charset=utf-8" },
          });
        } catch (e) {
          return new Response(blogListHTML([], activeCategory, activeTag), {
            headers: { "Content-Type": "text/html; charset=utf-8" },
          });
        }
      }
      return new Response(blogListHTML([], activeCategory, activeTag), {
        headers: { "Content-Type": "text/html; charset=utf-8" },
      });
    }

    // POST /api/blog/generate-image - Generate image for a post (separate call to avoid timeout)
    if (url.pathname === "/api/blog/generate-image" && request.method === "POST") {
      const blogKey = request.headers.get("X-Blog-Key");
      if (!blogKey || blogKey !== env.BLOG_SECRET) {
        return new Response(JSON.stringify({ error: "Unauthorized" }), { status: 401, headers: { "Content-Type": "application/json", ...corsHeaders } });
      }
      const { slug } = await request.json();
      if (!slug || !env.DB || !env.OPENAI_API_KEY) {
        return new Response(JSON.stringify({ error: "Missing slug, DB, or API key" }), { status: 400, headers: { "Content-Type": "application/json", ...corsHeaders } });
      }
      const post = await env.DB.prepare("SELECT title, category, synthesis FROM blog_posts WHERE slug = ?").bind(slug).first();
      if (!post) {
        return new Response(JSON.stringify({ error: "Post not found" }), { status: 404, headers: { "Content-Type": "application/json", ...corsHeaders } });
      }
      const imagePrompt = await generateSmartImagePrompt(post.title, post.synthesis || "", env);
      try {
        const imgResp = await fetch("https://api.openai.com/v1/images/generations", {
          method: "POST",
          headers: { "Content-Type": "application/json", "Authorization": "Bearer " + env.OPENAI_API_KEY },
          body: JSON.stringify({ model: "dall-e-3", prompt: imagePrompt, n: 1, size: "1792x1024", quality: "standard" }),
        });
        const imgData = await imgResp.json();
        const imgUrl = (imgData.data && imgData.data[0]) ? imgData.data[0].url : "";
        if (imgUrl) {
          await env.DB.prepare("UPDATE blog_posts SET image_url = ? WHERE slug = ?").bind(imgUrl, slug).run();
          return new Response(JSON.stringify({ slug, image_url: imgUrl }), { headers: { "Content-Type": "application/json", ...corsHeaders } });
        }
        return new Response(JSON.stringify({ error: "Image generation returned no URL", details: imgData }), { status: 500, headers: { "Content-Type": "application/json", ...corsHeaders } });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: { "Content-Type": "application/json", ...corsHeaders } });
      }
    }

    // GET /api/blog/posts - JSON list of published posts
    if (url.pathname === "/api/blog/posts" && request.method === "GET") {
      if (env.DB) {
        try {
          await ensureBlogTable(env.DB);
          const { results } = await env.DB.prepare(
            "SELECT id, slug, title, question, created_at, category, tags FROM blog_posts WHERE published = 1 ORDER BY created_at DESC"
          ).all();
          return new Response(JSON.stringify(results || []), {
            headers: { "Content-Type": "application/json", ...corsHeaders },
          });
        } catch (e) {
          return new Response(JSON.stringify({ error: e.message }), {
            status: 500, headers: { "Content-Type": "application/json", ...corsHeaders },
          });
        }
      }
      return new Response(JSON.stringify([]), {
        headers: { "Content-Type": "application/json", ...corsHeaders },
      });
    }

    // POST /api/blog/generate - Protected endpoint to generate a blog post
    if (url.pathname === "/api/blog/generate" && request.method === "POST") {
      const blogKey = request.headers.get("X-Blog-Key");
      if (!blogKey || blogKey !== env.BLOG_SECRET) {
        return new Response(JSON.stringify({ error: "Unauthorized" }), {
          status: 401, headers: { "Content-Type": "application/json", ...corsHeaders },
        });
      }
      try {
        const body = await request.json();
        const question = body.question;
        if (!question || question.trim().length < 5) {
          return new Response(JSON.stringify({ error: "Question required (min 5 chars)" }), {
            status: 400, headers: { "Content-Type": "application/json", ...corsHeaders },
          });
        }
        const post = await generateBlogPost(question, env);
        return new Response(JSON.stringify(post), {
          headers: { "Content-Type": "application/json", ...corsHeaders },
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), {
          status: 500, headers: { "Content-Type": "application/json", ...corsHeaders },
        });
      }
    }

    // GET /blog/feed.xml - RSS feed
    if (url.pathname === "/blog/feed.xml" || url.pathname === "/blog/rss") {
      if (env.DB) {
        try {
          await ensureBlogTable(env.DB);
          const { results } = await env.DB.prepare(
            "SELECT slug, title, synthesis, created_at, category, tags FROM blog_posts WHERE published = 1 ORDER BY created_at DESC LIMIT 20"
          ).all();
          const baseUrl = url.origin;
          const items = (results || []).map(p => {
            const excerpt = (p.synthesis || "").replace(/SUMMARY:\s*/i, "").slice(0, 500);
            const cat = BLOG_CATEGORIES[p.category || "human"] || BLOG_CATEGORIES["human"];
            return `    <item>
      <title>${escapeXML(p.title)}</title>
      <link>${baseUrl}/blog/${p.slug}</link>
      <guid>${baseUrl}/blog/${p.slug}</guid>
      <pubDate>${new Date(p.created_at).toUTCString()}</pubDate>
      <description>${escapeXML(excerpt)}</description>
      <category>${escapeXML(cat.name)}</category>
    </item>`;
          }).join("\n");
          const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>The Right Questions</title>
    <link>${baseUrl}/blog</link>
    <description>Philosophical questions explored through 184 wisdom traditions. Deep comparative analysis of humanity's biggest questions.</description>
    <language>en</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <atom:link href="${baseUrl}/blog/feed.xml" rel="self" type="application/rss+xml"/>
${items}
  </channel>
</rss>`;
          return new Response(rss, {
            headers: { "Content-Type": "application/rss+xml; charset=utf-8" },
          });
        } catch (e) {
          return new Response("RSS feed error", { status: 500 });
        }
      }
      return new Response("RSS feed not available", { status: 404 });
    }

    // GET /sitemap.xml
    if (url.pathname === "/sitemap.xml") {
      const baseUrl = url.origin;
      let postUrls = "";
      if (env.DB) {
        try {
          await ensureBlogTable(env.DB);
          const { results } = await env.DB.prepare(
            "SELECT slug, created_at FROM blog_posts WHERE published = 1 ORDER BY created_at DESC"
          ).all();
          postUrls = (results || []).map(p => `  <url>
    <loc>${baseUrl}/blog/${p.slug}</loc>
    <lastmod>${(p.created_at || "").slice(0, 10)}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>`).join("\n");
        } catch (e) {}
      }
      const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>${baseUrl}/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>${baseUrl}/blog</loc>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>
${postUrls}
</urlset>`;
      return new Response(sitemap, {
        headers: { "Content-Type": "application/xml; charset=utf-8" },
      });
    }

    // GET /blog/:slug - Individual blog post
    if (url.pathname.startsWith("/blog/") && url.pathname !== "/blog/") {
      const slug = url.pathname.replace("/blog/", "").replace(/\/$/, "");
      if (env.DB && slug) {
        try {
          await ensureBlogTable(env.DB);
          const post = await env.DB.prepare(
            "SELECT * FROM blog_posts WHERE slug = ? AND published = 1"
          ).bind(slug).first();
          if (post) {
            // Fetch related posts (same category, different post)
            let relatedPosts = [];
            try {
              const { results: rp } = await env.DB.prepare(
                "SELECT slug, title FROM blog_posts WHERE published = 1 AND category = ? AND slug != ? ORDER BY created_at DESC LIMIT 3"
              ).bind(post.category || "human", slug).all();
              relatedPosts = rp || [];
            } catch (e) {}

            // Fetch prev/next posts
            let prevPost = null, nextPost = null;
            try {
              prevPost = await env.DB.prepare(
                "SELECT slug, title FROM blog_posts WHERE published = 1 AND created_at < ? ORDER BY created_at DESC LIMIT 1"
              ).bind(post.created_at).first();
            } catch (e) {}
            try {
              nextPost = await env.DB.prepare(
                "SELECT slug, title FROM blog_posts WHERE published = 1 AND created_at > ? ORDER BY created_at ASC LIMIT 1"
              ).bind(post.created_at).first();
            } catch (e) {}

            return new Response(blogPostHTML(post, relatedPosts, prevPost, nextPost), {
              headers: { "Content-Type": "text/html; charset=utf-8" },
            });
          }
        } catch (e) {
          console.error("Blog post error:", e);
        }
      }
      return new Response("Post not found", { status: 404 });
    }

    // ============================================================
    // End Blog Routes
    // ============================================================

    // API: Usage endpoint
    if (url.pathname === "/api/usage" && request.method === "GET") {
      const userId = url.searchParams.get("userId");
      if (!userId) {
        return new Response(JSON.stringify({ error: "Missing userId" }), {
          status: 400, headers: { "Content-Type": "application/json", ...corsHeaders },
        });
      }
      if (env.DB) {
        try {
          await ensureUsageTable(env.DB);
          const usage = await getUsage(env.DB, userId);
          const isFirstDay = usage.last_reset_day === usage.created_at;
          const freeMax = isFirstDay ? 10 : 5;
          return new Response(JSON.stringify({
            tier: usage.tier,
            queries_today: usage.queries_today,
            free_max: freeMax,
            pro_queries_remaining: usage.pro_queries_remaining,
            premium_queries_remaining: usage.premium_queries_remaining,
          }), {
            headers: { "Content-Type": "application/json", ...corsHeaders },
          });
        } catch (e) {
          return new Response(JSON.stringify({ error: e.message }), {
            status: 500, headers: { "Content-Type": "application/json", ...corsHeaders },
          });
        }
      }
      return new Response(JSON.stringify({ tier: "free", queries_today: 0, free_max: 10, pro_queries_remaining: 0, premium_queries_remaining: 0 }), {
        headers: { "Content-Type": "application/json", ...corsHeaders },
      });
    }

    // API: Activate tier (from Stripe redirect, one activation per userId)
    if (url.pathname === "/api/activate" && request.method === "POST") {
      try {
        const body = await request.json();
        const { tier, userId } = body;
        if (!tier || !userId || tier !== "pro") {
          return new Response(JSON.stringify({ error: "Invalid request" }), {
            status: 400, headers: { "Content-Type": "application/json", ...corsHeaders },
          });
        }
        if (env.DB) {
          // Track activations to prevent abuse
          await env.DB.prepare("CREATE TABLE IF NOT EXISTS activations (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, tier TEXT, created_at TEXT DEFAULT (datetime('now')))").run();
          // Check how many times this userId has activated (allow multiple purchases)
          const recent = await env.DB.prepare("SELECT COUNT(*) as cnt FROM activations WHERE user_id = ? AND created_at > datetime('now', '-1 minute')").bind(userId).first();
          if (recent && recent.cnt > 0) {
            return new Response(JSON.stringify({ error: "Already activated. Refresh the page." }), {
              status: 403, headers: { "Content-Type": "application/json", ...corsHeaders },
            });
          }
          // Log activation
          await env.DB.prepare("INSERT INTO activations (user_id, tier) VALUES (?, ?)").bind(userId, "pro").run();
          // Activate pro
          await ensureUsageTable(env.DB);
          await getUsage(env.DB, userId);
          await env.DB.prepare("UPDATE usage SET pro_queries_remaining = pro_queries_remaining + 100 WHERE user_id = ?").bind(userId).run();
          const updated = await getUsage(env.DB, userId);
          return new Response(JSON.stringify({ success: true, tier: "pro", remaining: updated.pro_queries_remaining }), {
            headers: { "Content-Type": "application/json", ...corsHeaders },
          });
        }
        return new Response(JSON.stringify({ error: "Database not available" }), {
          status: 500, headers: { "Content-Type": "application/json", ...corsHeaders },
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), {
          status: 500, headers: { "Content-Type": "application/json", ...corsHeaders },
        });
      }
    }

    // Stripe webhook: generate token when payment is completed
    if (url.pathname === "/api/stripe-webhook" && request.method === "POST") {
      try {
        const body = await request.json();
        // Stripe sends checkout.session.completed event
        if (body.type === "checkout.session.completed") {
          const token = crypto.randomUUID();
          if (env.DB) {
            await env.DB.prepare("CREATE TABLE IF NOT EXISTS pro_tokens (token TEXT PRIMARY KEY, used INTEGER DEFAULT 0, created_at TEXT DEFAULT (datetime('now')))").run();
            await env.DB.prepare("INSERT INTO pro_tokens (token) VALUES (?)").bind(token).run();
          }
          // Return token (Stripe will redirect user with this token)
          return new Response(JSON.stringify({ received: true, token }), {
            headers: { "Content-Type": "application/json" },
          });
        }
        return new Response(JSON.stringify({ received: true }), {
          headers: { "Content-Type": "application/json" },
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), {
          status: 500, headers: { "Content-Type": "application/json" },
        });
      }
    }

    // Admin: generate pro token manually
    if (url.pathname === "/api/admin/generate-token" && request.method === "POST") {
      const blogKey = request.headers.get("X-Blog-Key");
      if (!blogKey || blogKey !== env.BLOG_SECRET) {
        return new Response(JSON.stringify({ error: "Unauthorized" }), { status: 401, headers: { "Content-Type": "application/json", ...corsHeaders } });
      }
      const token = crypto.randomUUID();
      if (env.DB) {
        await env.DB.prepare("CREATE TABLE IF NOT EXISTS pro_tokens (token TEXT PRIMARY KEY, used INTEGER DEFAULT 0, created_at TEXT DEFAULT (datetime('now')))").run();
        await env.DB.prepare("INSERT INTO pro_tokens (token) VALUES (?)").bind(token).run();
      }
      return new Response(JSON.stringify({ token, url: `https://academia.vedicvault.org/?activate=${token}` }), {
        headers: { "Content-Type": "application/json", ...corsHeaders },
      });
    }

    // API: Ask a question
    if (url.pathname === "/api/ask" && request.method === "POST") {
      try {
        const body = await request.json();
        const context = body.context || "";
        const question = context ? `${context}\n\nFollow-up question: ${body.question}` : body.question;
        const requestedTraditions = body.traditions;
        let tier = body.tier || "free";
        const userId = request.headers.get("X-User-ID") || "";
        if (!question || question.trim().length < 5) {
          return new Response(
            JSON.stringify({ error: "La pregunta debe tener al menos 5 caracteres." }),
            { status: 400, headers: { "Content-Type": "application/json", ...corsHeaders } }
          );
        }

        // Check usage limits
        if (env.DB && userId) {
          await ensureUsageTable(env.DB);
          const usage = await getUsage(env.DB, userId);
          const limitCheck = checkLimit(usage, tier);
          if (!limitCheck.allowed) {
            return new Response(JSON.stringify(limitCheck), {
              status: 429, headers: { "Content-Type": "application/json", ...corsHeaders },
            });
          }
          if (limitCheck.degraded) tier = "free_degraded";
        }

        const questionHash = await hashQuestion(question + (requestedTraditions ? requestedTraditions.sort().join(",") : "all") + tier);

        // Check cache in D1
        if (env.DB) {
          try {
            const cached = await env.DB.prepare(
              "SELECT traditions_json, synthesis FROM responses WHERE question_hash = ?"
            ).bind(questionHash).first();

            if (cached) {
              return new Response(JSON.stringify({
                question,
                traditions: JSON.parse(cached.traditions_json),
                synthesis: cached.synthesis,
                cached: true,
              }), {
                headers: { "Content-Type": "application/json", ...corsHeaders },
              });
            }
          } catch (dbErr) {
            console.error("D1 read error:", dbErr);
          }
        }

        // Generate responses
        const allTraditions = requestedTraditions && requestedTraditions.length > 0
          ? requestedTraditions
          : getAllTraditions();
        // Bigger batches for models with large context, smaller for free tier
        const batchSize = 40;
        const batches = createBatches(allTraditions, batchSize);
        const allResponses = [];

        // Process ALL batches in parallel (not waves) to beat the 30s CPU limit
        const batchPromises = batches.map(async (batch) => {
          try {
            const prompt = buildBatchPrompt(question, batch, body.lang || "en", tier);
            const rawResponse = await callAI(env.AI, prompt, tier, env);
            const parsed = parseAIResponse(rawResponse);
            if (parsed && Array.isArray(parsed) && parsed.length > 0) {
              return parsed;
            }
            if (rawResponse && rawResponse.length > 20) {
              return batch.map(t => {
                const regex = new RegExp(`${t}[:\\s]*([^\\n]+(?:\\n(?![A-Z])[^\\n]*)*)`, 'i');
                const match = rawResponse.match(regex);
                return {
                  tradition: t,
                  response: match ? match[1].trim().slice(0, 300) : "Respuesta no disponible."
                };
              });
            }
            return batch.map(t => ({ tradition: t, response: "Respuesta no disponible." }));
          } catch (e) {
            return batch.map(t => ({ tradition: t, response: "Error al consultar esta tradicion." }));
          }
        });

        const batchResults = await Promise.all(batchPromises);
        for (const results of batchResults) {
          allResponses.push(...results);
        }

        // Match LLM responses to requested traditions using fuzzy matching
        const filteredResponses = [];
        const matched = new Set();

        for (const requested of allTraditions) {
          let bestMatch = null;
          for (const r of allResponses) {
            if (!r || !r.tradition || !r.response) continue;
            if (namesMatch(requested, r.tradition) && !matched.has(r)) {
              bestMatch = r;
              break;
            }
          }
          if (bestMatch) {
            matched.add(bestMatch);
            filteredResponses.push({ tradition: requested, response: bestMatch.response });
          } else {
            filteredResponses.push({
              tradition: requested,
              response: "No se pudo generar una respuesta para esta tradicion."
            });
          }
        }

        // Generate synthesis
        const synthesisPrompt = buildSynthesisPrompt(question, filteredResponses, body.lang || "en");
        const synthesis = await callAI(env.AI, synthesisPrompt, tier, env);

        // Decrement query after successful processing
        if (env.DB && userId) {
          await decrementQuery(env.DB, userId, tier);
        }

        // Cache in D1
        if (env.DB) {
          try {
            await env.DB.prepare(
              "INSERT OR REPLACE INTO responses (question_hash, question, traditions_json, synthesis) VALUES (?, ?, ?, ?)"
            ).bind(
              questionHash,
              question,
              JSON.stringify(filteredResponses),
              synthesis
            ).run();
          } catch (dbErr) {
            console.error("D1 write error:", dbErr);
          }
        }

        return new Response(JSON.stringify({
          question,
          tier_used: tier,
          traditions: filteredResponses,
          synthesis,
          cached: false,
        }), {
          headers: { "Content-Type": "application/json", ...corsHeaders },
        });

      } catch (err) {
        console.error("API error:", err);
        return new Response(JSON.stringify({
          error: "Error al procesar la pregunta: " + err.message
        }), {
          status: 500,
          headers: { "Content-Type": "application/json", ...corsHeaders },
        });
      }
    }

    // API: Streaming endpoint for progress
    if (url.pathname === "/api/ask-stream" && request.method === "POST") {
      try {
        const body = await request.json();
        const context = body.context || "";
        const question = context ? `${context}\n\nFollow-up question: ${body.question}` : body.question;
        const requestedTraditions = body.traditions;
        let tier = body.tier || "free";
        const userId = request.headers.get("X-User-ID") || "";
        if (!question || question.trim().length < 5) {
          return new Response(
            JSON.stringify({ error: "La pregunta debe tener al menos 5 caracteres." }),
            { status: 400, headers: { "Content-Type": "application/json", ...corsHeaders } }
          );
        }

        // Check usage limits
        if (env.DB && userId) {
          await ensureUsageTable(env.DB);
          const usage = await getUsage(env.DB, userId);
          const limitCheck = checkLimit(usage, tier);
          if (!limitCheck.allowed) {
            return new Response(JSON.stringify(limitCheck), {
              status: 429, headers: { "Content-Type": "application/json", ...corsHeaders },
            });
          }
          if (limitCheck.degraded) tier = "free_degraded";
        }

        const questionHash = await hashQuestion(question + (requestedTraditions ? requestedTraditions.sort().join(",") : "all"));

        // Check cache
        if (env.DB) {
          try {
            const cached = await env.DB.prepare(
              "SELECT traditions_json, synthesis FROM responses WHERE question_hash = ?"
            ).bind(questionHash).first();

            if (cached) {
              return new Response(JSON.stringify({
                question,
                traditions: JSON.parse(cached.traditions_json),
                synthesis: cached.synthesis,
                cached: true,
              }), {
                headers: { "Content-Type": "application/json", ...corsHeaders },
              });
            }
          } catch (dbErr) {
            console.error("D1 read error:", dbErr);
          }
        }

        // Use ReadableStream for progress updates
        const { readable, writable } = new TransformStream();
        const writer = writable.getWriter();
        const encoder = new TextEncoder();

        const sendEvent = async (data) => {
          await writer.write(encoder.encode(`data: ${JSON.stringify(data)}\n\n`));
        };

        // Process in background
        const processQuestion = async () => {
          try {
            const allTraditions = requestedTraditions && requestedTraditions.length > 0
              ? requestedTraditions
              : getAllTraditions();
            const batchSize = 40;
            const batches = createBatches(allTraditions, batchSize);
            const allResponses = [];

            const lang = body.lang || "en";

            // Step 1: Generate all tradition responses in parallel, stream each batch to frontend
            const batchPromises = batches.map(async (batch) => {
              try {
                const prompt = buildBatchPrompt(question, batch, lang, tier);
                const rawResponse = await callAI(env.AI, prompt, tier, env);
                const parsed = parseAIResponse(rawResponse);
                let results;
                if (parsed && Array.isArray(parsed) && parsed.length > 0) {
                  results = parsed;
                } else if (rawResponse && rawResponse.length > 20) {
                  results = batch.map(t => {
                    const regex = new RegExp(`${t}[:\\s]*([^\\n]+(?:\\n(?![A-Z])[^\\n]*)*)`, 'i');
                    const match = rawResponse.match(regex);
                    return { tradition: t, response: match ? match[1].trim().slice(0, 300) : "Respuesta no disponible." };
                  });
                } else {
                  results = batch.map(t => ({ tradition: t, response: "Respuesta no disponible." }));
                }
                allResponses.push(...results);
                // Send each tradition individually for gradual appearance
                for (const r of results) {
                  await sendEvent({
                    type: "tradition",
                    tradition: r,
                    progress: allResponses.length,
                    total: allTraditions.length,
                  });
                }
                return results;
              } catch (e) {
                const fallback = batch.map(t => ({ tradition: t, response: "Error." }));
                allResponses.push(...fallback);
                return fallback;
              }
            });

            // Wait for ALL traditions to complete
            await Promise.all(batchPromises);

            // Fill in any missing traditions with placeholders
            for (const t of allTraditions) {
              const found = allResponses.some(r => {
                if (!r || !r.tradition) return false;
                return namesMatch(t, r.tradition);
              });
              if (!found) {
                const placeholder = { tradition: t, response: "Response not available for this tradition." };
                allResponses.push(placeholder);
                await sendEvent({ type: "tradition", tradition: placeholder, progress: allResponses.length, total: allTraditions.length });
              }
            }

            // Step 2: Generate synthesis + essay in parallel
            await sendEvent({ type: "status", message: "Generating synthesis and essay..." });
            const synthesisPrompt = buildSynthesisPrompt(question, allResponses, lang);

            const top15 = allResponses
              .filter(r => r.response && !r.response.includes("not available") && !r.response.includes("Error"))
              .slice(0, 15)
              .map(r => `${r.tradition}: ${r.response.slice(0, 200)}`)
              .join("\n");

            const essayPrompt = `You are a philosophical essayist writing for an academic journal.

Question: "${question}"

Top tradition responses:
${top15}

Write a 500-700 word essay that:
- Opens with a compelling hook (NEVER start with "Across traditions" or generic openings)
- Weaves together the most interesting responses into a flowing narrative
- Mentions specific traditions BY NAME
- Highlights surprising convergences and tensions naturally
- Ends with a thought-provoking reflection
- Reads like a New Yorker essay, not a research report
- NO section headers, NO bullet points, NO numbering -- just flowing prose
- NO markdown formatting`;

            const [synthesis, essay] = await Promise.all([
              callAI(env.AI, synthesisPrompt, tier, env),
              callAI(env.AI, essayPrompt, tier, env).catch(() => ""),
            ]);

            await sendEvent({ type: "essay", essay });
            await sendEvent({ type: "synthesis", synthesis });

            // Decrement query after successful processing
            if (env.DB && userId) {
              await decrementQuery(env.DB, userId, tier);
            }

            // Cache
            if (env.DB) {
              try {
                await env.DB.prepare(
                  "INSERT OR REPLACE INTO responses (question_hash, question, traditions_json, synthesis) VALUES (?, ?, ?, ?)"
                ).bind(questionHash, question, JSON.stringify(allResponses), synthesis).run();
              } catch (dbErr) {
                console.error("D1 write error:", dbErr);
              }
            }

            await sendEvent({
              type: "complete",
              question,
              synthesis,
              cached: false,
            });
          } catch (err) {
            await sendEvent({ type: "error", error: err.message });
          } finally {
            await writer.close();
          }
        };

        // Don't await - let it stream
        processQuestion();

        return new Response(readable, {
          headers: {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            ...corsHeaders,
          },
        });

      } catch (err) {
        return new Response(JSON.stringify({ error: err.message }), {
          status: 500,
          headers: { "Content-Type": "application/json", ...corsHeaders },
        });
      }
    }

    // API: Get cached response by hash
    if (url.pathname.startsWith("/api/cached/") && request.method === "GET") {
      const hash = url.pathname.split("/api/cached/")[1];
      if (!hash || hash.length < 8) {
        return new Response(JSON.stringify({ error: "Invalid hash" }), {
          status: 400, headers: { "Content-Type": "application/json", ...corsHeaders },
        });
      }
      if (env.DB) {
        try {
          const cached = await env.DB.prepare(
            "SELECT question, traditions_json, synthesis FROM responses WHERE question_hash = ?"
          ).bind(hash).first();
          if (cached) {
            return new Response(JSON.stringify({
              question: cached.question,
              traditions: JSON.parse(cached.traditions_json),
              synthesis: cached.synthesis,
              cached: true,
            }), {
              headers: { "Content-Type": "application/json", ...corsHeaders },
            });
          }
        } catch (dbErr) {
          console.error("D1 read error:", dbErr);
        }
      }
      return new Response(JSON.stringify({ error: "Not found" }), {
        status: 404, headers: { "Content-Type": "application/json", ...corsHeaders },
      });
    }

    // Share link redirect: /s/:hash -> /?q=:hash
    if (url.pathname.startsWith("/s/")) {
      const hash = url.pathname.split("/s/")[1];
      const langParam = url.searchParams.get("lang");
      const redirectUrl = new URL(url.origin);
      redirectUrl.searchParams.set("q", hash);
      if (langParam) redirectUrl.searchParams.set("lang", langParam);
      return Response.redirect(redirectUrl.toString(), 302);
    }

    // Fallback: serve static assets
    if (env.ASSETS) {
      return env.ASSETS.fetch(request);
    }

    return new Response("Not found", { status: 404, headers: corsHeaders });
  },

  // ============================================================
  // Scheduled (Cron) Handler - Auto-generate blog posts daily
  // Rotates categories to ensure variety
  // ============================================================
  async scheduled(event, env, ctx) {
    console.log("Cron triggered: generating daily blog post");
    try {
      if (!env.DB) {
        console.error("No DB binding available for cron");
        return;
      }

      await ensureBlogTable(env.DB);

      // Get all already-published slugs and the last published category
      const { results: existing } = await env.DB.prepare(
        "SELECT slug, category FROM blog_posts ORDER BY created_at DESC"
      ).all();
      const publishedSlugs = new Set((existing || []).map(r => r.slug));
      const lastCategory = (existing && existing.length > 0) ? (existing[0].category || "") : "";

      // Build list of unpublished questions with their categories
      const unpublished = [];
      for (const q of BLOG_QUESTIONS) {
        const slug = generateSlug(q);
        if (!publishedSlugs.has(slug)) {
          unpublished.push({ question: q, category: categorizeQuestion(q) });
        }
      }

      if (unpublished.length === 0) {
        console.log("All blog questions have been published.");
        return;
      }

      // Prefer a question from a DIFFERENT category than the last published post
      let nextQuestion = null;
      if (lastCategory) {
        const differentCategory = unpublished.find(u => u.category !== lastCategory);
        if (differentCategory) {
          nextQuestion = differentCategory.question;
        }
      }
      // Fallback: just pick the first unpublished
      if (!nextQuestion) {
        nextQuestion = unpublished[0].question;
      }

      console.log("Generating blog post for:", nextQuestion);
      const post = await generateBlogPost(nextQuestion, env);
      console.log("Blog post generated:", post.slug, "category:", post.category);

      // Generate image in a separate step (to avoid timeout)
      if (env.OPENAI_API_KEY && post.slug) {
        try {
          const safeTitle = post.title.replace(/suffering|death|evil|violence|war|kill|anger|hate/gi, "contemplation");
          const imagePrompt = generateImagePromptFromContent(safeTitle, post.category || "human", post.synthesis || "");
          const imgResp = await fetch("https://api.openai.com/v1/images/generations", {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": "Bearer " + env.OPENAI_API_KEY },
            body: JSON.stringify({ model: "dall-e-3", prompt: imagePrompt, n: 1, size: "1792x1024", quality: "standard" }),
          });
          const imgData = await imgResp.json();
          const imgUrl = (imgData.data && imgData.data[0]) ? imgData.data[0].url : "";
          if (imgUrl) {
            await env.DB.prepare("UPDATE blog_posts SET image_url = ? WHERE slug = ?").bind(imgUrl, post.slug).run();
            console.log("Image generated for:", post.slug);
          }
        } catch (imgErr) {
          console.error("Image generation failed:", imgErr.message);
        }
      }
    } catch (e) {
      console.error("Cron blog generation failed:", e.message);
    }
  },
};
