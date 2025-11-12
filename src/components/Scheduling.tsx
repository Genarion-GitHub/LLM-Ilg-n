import React, { useState } from 'react';
import { ChevronLeftIcon, ChevronRightIcon, RocketIcon, CalendarIcon } from './Icons';

interface SchedulingProps {
    onStart: () => void;
    onScheduleLater: () => void;
}

const Scheduling: React.FC<SchedulingProps> = ({ onStart, onScheduleLater }) => {
    const [selectedDate, setSelectedDate] = useState(new Date()); // Bugünün tarihi
    const [selectedTime, setSelectedTime] = useState('10:00');

    const monthNames = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];
    const dayNames = ['P', 'S', 'Ç', 'P', 'C', 'C', 'P'];
    const timeSlots = ['09:00', '09:30', '10:00', '10:30', '11:00', '14:00', '14:30', '15:00', '15:30'];

    const renderCalendarDays = () => {
        const year = selectedDate.getFullYear();
        const month = selectedDate.getMonth();
        const firstDayOfMonth = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();

        const days = [];
        for (let i = 0; i < (firstDayOfMonth + 6) % 7; i++) {
            days.push(<div key={`empty-${i}`} className="text-center p-2"></div>);
        }

        for (let day = 1; day <= daysInMonth; day++) {
            const isSelected = day === selectedDate.getDate();
            days.push(
                <div key={day} className="text-center p-2">
                    <button
                        onClick={() => setSelectedDate(new Date(year, month, day))}
                        className={`w-8 h-8 rounded-full flex items-center justify-center transition-colors duration-200 ${
                            isSelected ? 'bg-[#58b0b8] text-white' : 'hover:bg-gray-200'
                        }`}
                    >
                        {day}
                    </button>
                </div>
            );
        }
        return days;
    };

    const changeMonth = (offset: number) => {
        const newDate = new Date(selectedDate);
        newDate.setMonth(selectedDate.getMonth() + offset, 1); // set to 1 to avoid day-of-month issues
        setSelectedDate(newDate);
    };

    return (
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-4xl w-full">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Left Side: Calendar and Actions */}
                <div className="flex flex-col">
                    <h2 className="text-2xl font-bold text-gray-800 mb-4">Mülakatınızı Planlayın</h2>
                    <div className="bg-gray-50 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-4">
                            <button onClick={() => changeMonth(-1)} className="p-1 rounded-full hover:bg-gray-200">
                                <ChevronLeftIcon className="w-6 h-6 text-gray-600" />
                            </button>
                            <h3 className="text-lg font-semibold">{`${monthNames[selectedDate.getMonth()]} ${selectedDate.getFullYear()}`}</h3>
                            <button onClick={() => changeMonth(1)} className="p-1 rounded-full hover:bg-gray-200">
                                <ChevronRightIcon className="w-6 h-6 text-gray-600" />
                            </button>
                        </div>
                        <div className="grid grid-cols-7 gap-1 text-sm text-gray-500 mb-2">
                            {dayNames.map((day, index) => <div key={`${day}-${index}`} className="text-center font-medium">{day}</div>)}
                        </div>
                        <div className="grid grid-cols-7 gap-1 text-sm">
                            {renderCalendarDays()}
                        </div>
                    </div>
                </div>

                {/* Right Side: Time Selection */}
                <div className="flex flex-col">
                    <h2 className="text-2xl font-bold text-gray-800 mb-4">Mülakatınız Sizi Bekliyor</h2>
                    <h3 className="text-lg font-semibold text-gray-700 mb-4">Bir Zaman Dilimi Seçin</h3>
                    <div className="grid grid-cols-3 gap-3 mb-4">
                        {timeSlots.map(time => (
                            <button
                                key={time}
                                onClick={() => setSelectedTime(time)}
                                className={`px-4 py-2 rounded-lg border-2 transition-colors duration-200 ${
                                    selectedTime === time ? 'bg-[#58b0b8] text-white border-[#58b0b8]' : 'bg-white text-gray-700 border-gray-300 hover:border-[#58b0b8]'
                                }`}
                            >
                                {time}
                            </button>
                        ))}
                    </div>
                    <p className="text-sm text-gray-500 mb-6">
                        Mülakatınızı daha sonra yapmak için takvimden uygun bir tarih ve saat seçin. Hazırsanız, mülakata ve entegre quize hemen başlayabilirsiniz.
                    </p>
                    <div className="mt-auto space-y-3">
                         <button
                            onClick={onStart}
                            className="w-full bg-[#58b0b8] text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 hover:bg-opacity-90 transition-opacity"
                        >
                            <RocketIcon className="w-5 h-5" />
                            Mülakata Hızlı Başla
                        </button>
                        <button 
                            onClick={() => {
                                const [hours, minutes] = selectedTime.split(':').map(Number);
                                const scheduledDateTime = new Date(selectedDate);
                                scheduledDateTime.setHours(hours, minutes, 0, 0);
                                
                                // Geçmiş tarih kontrolü
                                const now = new Date();
                                if (scheduledDateTime <= now) {
                                    alert('Geçmiş bir tarih ve saat seçemezsiniz. Lütfen gelecek bir zaman seçin.');
                                    return;
                                }
                                
                                // localStorage'a kaydet
                                localStorage.setItem('scheduledInterview', JSON.stringify({
                                    date: selectedDate.toISOString(),
                                    time: selectedTime,
                                    scheduledDateTime: scheduledDateTime.toISOString()
                                }));
                                
                                onScheduleLater();
                            }}
                            className="w-full bg-gray-200 text-gray-700 font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 hover:bg-gray-300 transition-colors"
                        >
                            <CalendarIcon className="w-5 h-5" />
                            Planla: {selectedDate.toLocaleDateString('tr-TR')} {selectedTime}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Scheduling;