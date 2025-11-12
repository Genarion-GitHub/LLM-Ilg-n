import React, { useState, useEffect } from 'react';
import { SpinnerIcon, ClockIcon } from './Icons';

interface WaitingRoomProps {
    onCountdownFinish: () => void;
}

const WaitingRoom: React.FC<WaitingRoomProps> = ({ onCountdownFinish }) => {
    const [scheduledDateTime, setScheduledDateTime] = useState<Date | null>(null);
    const [currentTime, setCurrentTime] = useState(new Date());
    const [isConfirming, setIsConfirming] = useState(true);
    const [chatStarted, setChatStarted] = useState(false);
    
    useEffect(() => {
        // localStorage'dan zamanlanmış mülakat bilgisini al
        const scheduled = localStorage.getItem('scheduledInterview');
        if (scheduled) {
            const data = JSON.parse(scheduled);
            setScheduledDateTime(new Date(data.scheduledDateTime));
        }
        
        // Onay mesajını 3 saniye göster
        const timer = setTimeout(() => {
            setIsConfirming(false);
        }, 3000);

        return () => clearTimeout(timer);
    }, []);
    
    useEffect(() => {
        // Her saniye güncelle
        const interval = setInterval(() => {
            setCurrentTime(new Date());
        }, 1000);
        
        return () => clearInterval(interval);
    }, []);
    
    useEffect(() => {
        if (!scheduledDateTime || chatStarted) return;
        
        const now = currentTime.getTime();
        const scheduled = scheduledDateTime.getTime();
        const timeUntilInterview = scheduled - now;
        
        // Mülakat saatinden 1 dakika önce chatbot'u başlat
        if (timeUntilInterview <= 60000 && timeUntilInterview > 0 && !chatStarted) {
            console.log('🟢 1 dakika kaldı, chatbot başlatılıyor...');
            setChatStarted(true);
            onCountdownFinish();
        }
    }, [currentTime, scheduledDateTime, chatStarted, onCountdownFinish]);
    
    // 5 dakikadan az kaldıysa geri sayımı göster, değilse bekle
    if (!scheduledDateTime) {
        return (
            <div className="bg-white rounded-2xl shadow-xl p-12 max-w-lg w-full text-center flex flex-col items-center">
                <SpinnerIcon className="w-12 h-12 text-[#58b0b8]" />
                <h2 className="text-2xl font-bold text-gray-800 mt-6">Yükleniyor...</h2>
                <p className="text-gray-600 mt-2">Lütfen bekleyiniz...</p>
            </div>
        );
    }
    
    const timeUntilInterview = scheduledDateTime.getTime() - currentTime.getTime();
    
    // 5 dakikadan fazla varsa bekle
    if (timeUntilInterview > 300000) {
        const minutesLeft = Math.floor(timeUntilInterview / 60000);
        return (
            <div className="bg-white rounded-2xl shadow-xl p-12 max-w-lg w-full text-center flex flex-col items-center">
                <ClockIcon className="w-12 h-12 text-[#58b0b8]" />
                <h2 className="text-2xl font-bold text-gray-800 mt-6">Mülakat Zamanlandı</h2>
                <p className="text-gray-600 mt-4">Mülakatınız {scheduledDateTime.toLocaleString('tr-TR')} tarihinde başlayacak.</p>
                <p className="text-4xl font-bold text-[#58b0b8] my-4">{minutesLeft} dakika</p>
                <p className="text-gray-500 text-sm">Geri sayım 5 dakika kala başlayacak.</p>
            </div>
        );
    }
    
    const getTimeLeft = () => {
        if (!scheduledDateTime) return 0;
        const diff = scheduledDateTime.getTime() - currentTime.getTime();
        return Math.max(0, Math.floor(diff / 1000));
    };
    
    const timeLeft = getTimeLeft();



    const formatTime = (seconds: number) => {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${String(minutes).padStart(2, '0')}:${String(remainingSeconds).padStart(2, '0')}`;
    };

    if (isConfirming) {
        return (
            <div className="bg-white rounded-2xl shadow-xl p-12 max-w-lg w-full text-center flex flex-col items-center">
                <SpinnerIcon className="w-12 h-12 text-[#58b0b8]" />
                <h2 className="text-2xl font-bold text-gray-800 mt-6">Talebiniz Alındı</h2>
                <p className="text-gray-600 mt-2">Lütfen bekleyiniz, mülakatınız için hazırlık yapılıyor...</p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-2xl shadow-xl p-12 max-w-lg w-full text-center flex flex-col items-center">
             <ClockIcon className="w-12 h-12 text-[#58b0b8]" />
             <h2 className="text-2xl font-bold text-gray-800 mt-6">Mülakatınız Başlamak Üzere</h2>
             <p className="text-gray-500 mt-2">Mülakata kalan süre:</p>
             <p className="text-7xl font-bold text-[#58b0b8] my-4 tracking-wider">{formatTime(timeLeft)}</p>
             <p className="text-gray-600 mt-4">Lütfen hazır olun. Süre dolduğunda mülakat başlayacak.</p>
        </div>
    );
};

export default WaitingRoom;
