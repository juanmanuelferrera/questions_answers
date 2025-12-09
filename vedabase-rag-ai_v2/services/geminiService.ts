import { GoogleGenAI, Type, Schema } from "@google/genai";
import { SearchResponse } from "../types";

const genAI = new GoogleGenAI({ apiKey: process.env.API_KEY });

const responseSchema: Schema = {
  type: Type.OBJECT,
  properties: {
    answer: {
      type: Type.STRING,
      description: "A synthesized answer to the user's spiritual question based on Vedic wisdom. Around 150-200 words.",
    },
    sources: {
      type: Type.ARRAY,
      description: "A list of 3 to 5 relevant sources from books like Bhagavad Gita or Srimad Bhagavatam that support the answer.",
      items: {
        type: Type.OBJECT,
        properties: {
          book: { type: Type.STRING, description: "The name of the book (e.g., Srimad Bhagavatam Canto 1)" },
          chapterVerse: { type: Type.STRING, description: "The chapter and verse reference (e.g., Chapter 2, Verse 14)" },
          sanskrit: { type: Type.STRING, description: "The sanskrit sloka text (optional but preferred)" },
          translation: { type: Type.STRING, description: "The English translation of the verse or excerpt." },
          relevance: { type: Type.NUMBER, description: "A relevance score between 70 and 99 representing how well this matches the query." }
        },
        required: ["book", "chapterVerse", "translation", "relevance"]
      }
    },
    relatedTopics: {
      type: Type.ARRAY,
      description: "A list of 3-5 related spiritual concepts or topics for further exploration.",
      items: { type: Type.STRING }
    }
  },
  required: ["answer", "sources", "relatedTopics"]
};

export const searchVedabase = async (query: string): Promise<SearchResponse> => {
  try {
    const modelId = "gemini-2.5-flash"; // Using flash for speed
    const prompt = `
      You are an expert Vedabase assistant with deep knowledge of Srila Prabhupada's books (Bhagavad-gita, Srimad Bhagavatam, Chaitanya Charitamrita).
      
      The user asks: "${query}"

      Please provide:
      1. A profound, philosophically accurate summary answer based on the teachings.
      2. 3 to 5 specific "sources" that would realistically be retrieved from a vector database for this query. 
         Include the Sanskrit if possible. 
         Fake the "relevance" score to look like a float (e.g., 94.5).
      3. 4 short, interesting "Related Topics" or concepts the user might want to explore next based on this answer.
    `;

    const result = await genAI.models.generateContent({
      model: modelId,
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: responseSchema,
        temperature: 0.3, // Keep it focused and accurate
      }
    });

    if (result.text) {
      return JSON.parse(result.text) as SearchResponse;
    }
    
    throw new Error("No content generated");

  } catch (error) {
    console.error("Gemini Search Error:", error);
    throw error;
  }
};

export const translateText = async (text: string, targetLang: string): Promise<string> => {
  try {
    const modelId = "gemini-2.5-flash";
    const prompt = `Translate the following spiritual text into ${targetLang}. Keep the tone respectful and accurate to the philosophy: \n\n"${text}"`;
    
    const result = await genAI.models.generateContent({
      model: modelId,
      contents: prompt,
    });
    
    return result.text || text;
  } catch (e) {
    console.error("Translation failed", e);
    return text;
  }
};