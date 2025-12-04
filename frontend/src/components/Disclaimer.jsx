import React from 'react';
import { AlertTriangle } from 'lucide-react';

export default function Disclaimer({ compact = false }) {
    if (compact) {
        return (
            <div className="w-full max-w-4xl mx-auto mb-6 p-4 bg-yellow-500/5 border border-yellow-500/20 rounded-xl">
                <div className="flex gap-3 items-start">
                    <AlertTriangle size={20} className="text-yellow-500 shrink-0 mt-0.5" />
                    <div className="space-y-1">
                        <h4 className="text-sm font-semibold text-yellow-500">Risk Disclaimer</h4>
                        <p className="text-xs text-gray-400 leading-relaxed">
                            Trading cryptocurrencies involves significant risk and can result in the loss of your capital.
                            You should not invest more than you can afford to lose and should ensure that you fully understand the risks involved.
                            Past performance is not indicative of future results. This software is provided for informational purposes only.
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="w-full p-6 bg-yellow-500/5 border border-yellow-500/20 rounded-2xl mb-8">
            <div className="flex gap-4 items-start">
                <AlertTriangle size={24} className="text-yellow-500 shrink-0 mt-1" />
                <div className="space-y-2">
                    <h4 className="text-base font-bold text-yellow-500">
                        Important Risk Warning
                    </h4>
                    <p className="text-sm text-gray-400 leading-relaxed">
                        Trading cryptocurrencies and other financial instruments involves substantial risk of loss and is not suitable for every investor.
                        The valuation of cryptocurrencies and related products may fluctuate; such changes may be significant and may occur rapidly and without warning.
                        Past performance is not indicative of future results. You should carefully consider whether trading is suitable for you in light of your circumstances, knowledge, and financial resources.
                        Use this software at your own risk. The developers assume no responsibility for any trading losses incurred.
                    </p>
                </div>
            </div>
        </div>
    );
}
