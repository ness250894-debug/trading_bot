import React from 'react';
import { AlertTriangle } from 'lucide-react';

export default function Disclaimer({ compact = false }) {
    if (compact) {
        return (
            <div style={{
                padding: '0.75rem 1rem',
                background: 'rgba(234, 179, 8, 0.05)',
                border: '1px solid rgba(234, 179, 8, 0.2)',
                borderRadius: '8px',
                marginBottom: '1rem'
            }}>
                <p style={{
                    fontSize: '11px',
                    color: '#a1a1aa',
                    margin: 0,
                    lineHeight: '1.4'
                }}>
                    <strong style={{ color: '#eab308' }}>⚠️ Risk Disclaimer:</strong> Trading involves substantial risk of loss. Past performance is not indicative of future results. Use at your own risk.
                </p>
            </div>
        );
    }

    return (
        <div style={{
            padding: '1rem 1.25rem',
            background: 'rgba(234, 179, 8, 0.05)',
            border: '1px solid rgba(234, 179, 8, 0.2)',
            borderRadius: '12px',
            marginBottom: '1.5rem'
        }}>
            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'start' }}>
                <AlertTriangle size={18} style={{ color: '#eab308', flexShrink: 0, marginTop: '2px' }} />
                <div>
                    <h4 style={{
                        fontSize: '13px',
                        fontWeight: '600',
                        color: '#eab308',
                        margin: '0 0 0.5rem 0'
                    }}>
                        Risk Disclaimer
                    </h4>
                    <p style={{
                        fontSize: '12px',
                        color: '#a1a1aa',
                        margin: 0,
                        lineHeight: '1.5'
                    }}>
                        Trading cryptocurrencies and other financial instruments involves substantial risk of loss and is not suitable for every investor. Past performance is not indicative of future results. You should carefully consider whether trading is suitable for you in light of your circumstances, knowledge, and financial resources. Use this software at your own risk.
                    </p>
                </div>
            </div>
        </div>
    );
}
