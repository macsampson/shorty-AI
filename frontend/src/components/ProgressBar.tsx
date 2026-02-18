import React from 'react';

interface ProgressBarProps {
  progress: number;
  stage: string;
  message: string;
}

const stageConfig: Record<string, { icon: string; color: string; label: string }> = {
  expansion: { icon: "🧠", color: "bg-blue-500", label: "Prompt Expansion" },
  generation: { icon: "🎬", color: "bg-purple-500", label: "Video Generation" },
  captions: { icon: "💬", color: "bg-green-500", label: "Caption Extraction" },
  overlay: { icon: "✨", color: "bg-yellow-500", label: "Caption Overlay" },
  complete: { icon: "✅", color: "bg-green-600", label: "Complete" },
  error: { icon: "❌", color: "bg-red-500", label: "Error" }
};

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  stage,
  message
}) => {
  const config = stageConfig[stage as keyof typeof stageConfig] || stageConfig.expansion;

  return (
    <div className="w-full p-6 bg-gray-800 rounded-lg shadow-lg mt-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-lg font-semibold text-white flex items-center gap-2">
          <span className="text-2xl">{config.icon}</span>
          {config.label}
        </span>
        <span className="text-xl font-bold text-white">
          {progress.toFixed(0)}%
        </span>
      </div>

      <div className="w-full bg-gray-700 rounded-full h-6 overflow-hidden mb-3">
        <div
          className={`h-full ${config.color} transition-all duration-300 ease-out flex items-center justify-end pr-2`}
          style={{ width: `${Math.min(progress, 100)}%` }}
        >
          {progress > 10 && (
            <span className="text-xs font-bold text-white">
              {progress.toFixed(0)}%
            </span>
          )}
        </div>
      </div>

      <p className="text-sm text-gray-300">{message}</p>
    </div>
  );
};
