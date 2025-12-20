import React from 'react';
import { Newspaper, RefreshCw } from 'lucide-react';

const NewsItem = ({ title, summary, source, time, url }) => (
    <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="block p-4 glass rounded-xl hover:bg-white/5 transition-all group border border-transparent hover:border-primary/20"
    >
        <div className="flex justify-between items-start mb-2">
            <h4 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors flex-1">
                {title}
            </h4>
            <span className="text-xs text-muted-foreground ml-2">{time}</span>
        </div>
        <p className="text-xs text-muted-foreground mb-2 line-clamp-2">{summary}</p>
        <span className="text-xs text-primary/60">{source}</span>
    </a>
);

const NewsFeed = ({ newsItems, loading, onRefresh }) => {
    return (
        <div className="glass p-6 rounded-2xl">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <Newspaper size={20} className="text-primary" />
                    <h2 className="text-xl font-bold">Market News</h2>
                </div>
                <button
                    onClick={onRefresh}
                    disabled={loading}
                    className="p-1.5 hover:bg-white/10 rounded-lg transition-all"
                    title="Refresh news"
                >
                    <RefreshCw size={16} className={`text-muted-foreground ${loading ? 'animate-spin' : ''}`} />
                </button>
            </div>

            <div className="max-h-[400px] overflow-y-auto space-y-3 pr-2 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent hover:scrollbar-thumb-white/20">
                {loading ? (
                    <div className="text-center py-12">
                        <div className="w-8 h-8 border-3 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                        <p className="text-muted-foreground text-sm">Loading news...</p>
                    </div>
                ) : newsItems && newsItems.length > 0 ? (
                    newsItems.map((item, idx) => (
                        <NewsItem key={idx} {...item} />
                    ))
                ) : (
                    <div className="text-center py-12">
                        <Newspaper size={48} className="mx-auto text-muted-foreground/30 mb-4" />
                        <p className="text-muted-foreground font-medium">No news available</p>
                        <p className="text-sm text-muted-foreground/60 mt-1">
                            Configure API keys in .env to enable news sources
                        </p>
                        <button
                            onClick={onRefresh}
                            className="mt-4 px-4 py-2 bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-all"
                        >
                            Retry
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default NewsFeed;
