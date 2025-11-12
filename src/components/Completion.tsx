import React from 'react';
import { CheckCircleIcon } from './Icons';

interface CompletionProps {
    score: number;
    totalQuestions: number;
    sessionId: string;
    onRestart: () => void;
}

const Completion: React.FC<CompletionProps> = ({ score, totalQuestions, sessionId, onRestart }) => {
    const [transcriptSaved, setTranscriptSaved] = React.useState(false);
    
    React.useEffect(() => {
        // Transcript'i kaydet
        const saveTranscript = async () => {
            try {
                const response = await fetch('http://localhost:5001/api/save-transcript', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        sessionId: sessionId,
                        userMessage: '' // Boş mesaj, sadece transcript kaydetmek için
                    })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    console.log('✅ Transcript kaydedildi:', data);
                    setTranscriptSaved(true);
                }
            } catch (error) {
                console.error('❌ Transcript kaydetme hatası:', error);
            }
        };
        
        saveTranscript();
    }, [sessionId]);
    return (
        <div className="bg-white rounded-2xl shadow-xl p-12 max-w-lg w-full text-center flex flex-col items-center">
            <CheckCircleIcon className="w-16 h-16 text-green-500" />
            <h2 className="text-3xl font-bold text-gray-800 mt-6">Mülakat Tamamlandı!</h2>
            <p className="text-gray-600 mt-6 mb-8">Mülakatınız başarıyla tamamlandı. Değerlendirme sonuçlarınız en kısa sürede size iletilecektir. Zaman ayırdığınız için teşekkür ederiz.</p>
            {transcriptSaved && (
                <p className="text-sm text-green-600 mb-4">✓ Mülakat kaydınız başarıyla kaydedildi.</p>
            )}
            <div className="space-y-3">
                <button
                    onClick={onRestart}
                    className="w-full bg-[#58b0b8] text-white font-bold py-3 px-4 rounded-lg hover:bg-opacity-90 transition-opacity"
                >
                    Ana Sayfaya Dön
                </button>
            </div>
        </div>
    );
};

export default Completion;
