export type Page = 'scheduling' | 'chatbot' | 'interview' | 'quiz' | 'qna' | 'waiting' | 'completion';

export interface ChatMessage {
  sender: 'user' | 'assistant';
  text: string;
}

export interface QuizQuestion {
  question: string;
  options: string[];
  correctAnswerIndex: number;
}