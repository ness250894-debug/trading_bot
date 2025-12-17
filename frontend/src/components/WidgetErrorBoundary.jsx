import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

class WidgetErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error("Widget Error:", error, errorInfo);
    }

    handleRetry = () => {
        this.setState({ hasError: false, error: null });
    };

    render() {
        if (this.state.hasError) {
            return (
                <div className="h-full w-full min-h-[200px] flex flex-col items-center justify-center p-6 bg-red-500/5 rounded-xl border border-red-500/20 text-center">
                    <div className="bg-red-500/10 p-3 rounded-full mb-3">
                        <AlertTriangle className="text-red-500" size={24} />
                    </div>
                    <h3 className="text-lg font-semibold text-red-500 mb-1">Widget Error</h3>
                    <p className="text-sm text-red-400/80 mb-4 max-w-[250px]">
                        This component failed to render.
                    </p>
                    <button
                        onClick={this.handleRetry}
                        className="flex items-center gap-2 px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 rounded-lg text-sm font-medium transition-colors"
                    >
                        <RefreshCw size={14} />
                        Retry
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}

export default WidgetErrorBoundary;
