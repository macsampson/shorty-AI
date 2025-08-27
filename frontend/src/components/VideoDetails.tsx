import React, { useState } from "react"
import { GeneratedContent } from "../types"
import { formatFolderTitle } from "../utils/formatters"

interface VideoDetailsProps {
  selectedFolder: string
  generatedContent: GeneratedContent | null
  videoGenerating: boolean
}

const VideoDetails: React.FC<VideoDetailsProps> = ({
  selectedFolder,
  generatedContent,
  videoGenerating,
}) => {
  const [isScriptMediaExpanded, setIsScriptMediaExpanded] = useState(false)

  if (videoGenerating) {
    return (
      <div className="flex flex-col justify-center items-center py-12 px-8 text-center">
        <div className="spinner"></div>
        <p className="mt-6 text-gray-600">
          Your video is being generated. This may take a few minutes.
        </p>
      </div>
    )
  }

  if (!generatedContent) {
    return (
      <div className="flex flex-col justify-center items-center py-12 px-8 text-center">
        <div className="spinner"></div>
        <p className="mt-6 text-gray-600">Loading video details...</p>
      </div>
    )
  }

  const hasVideo =
    generatedContent.video_urls && generatedContent.video_urls.length > 0

  return (
    <div className="flex flex-col gap-6">
      {/* Video section - shown first */}
      {hasVideo && (
        <div className="bg-white rounded-lg p-4 md:p-6 shadow-md flex flex-col items-center max-w-full overflow-hidden relative video-ready">
          <h3 className="text-xl font-semibold text-primary self-start mb-4">
            Video Preview
          </h3>
          <div className="w-full relative rounded-lg overflow-hidden bg-black flex justify-center items-center aspect-video max-h-[60vh]">
            <video
              controls
              src={`http://localhost:8000${generatedContent.video_urls[0]}`}
              playsInline
              preload="metadata"
              className="w-full h-full max-h-[60vh] rounded object-contain shadow-lg"
            />
          </div>
          <div className="flex justify-center mt-6 w-full">
            <button
              className="bg-primary hover:bg-primary-hover text-white border-none rounded px-6 py-3 text-base font-semibold cursor-pointer transition-all flex items-center shadow-md hover:translate-y-[-2px] hover:shadow-lg active:translate-y-0 active:shadow"
              onClick={() => {
                const link = document.createElement("a")
                link.href = `http://localhost:8000${generatedContent.video_urls[0]}`
                link.download = `${formatFolderTitle(selectedFolder)}.mp4`
                document.body.appendChild(link)
                link.click()
                document.body.removeChild(link)
              }}
            >
              <span className="mr-2">↓</span> Download Video
            </button>
          </div>
        </div>
      )}

      {/* Collapsible container for script and media */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div
          className="flex justify-between items-center p-4 md:p-6 cursor-pointer bg-gray-50 border-b border-gray-200 transition-colors hover:bg-gray-100"
          onClick={() => setIsScriptMediaExpanded(!isScriptMediaExpanded)}
        >
          <h3 className="text-lg font-medium text-primary m-0">
            Script & Media
          </h3>
          <span
            className="text-sm transition-transform duration-300"
            style={{
              transform: isScriptMediaExpanded
                ? "rotate(0deg)"
                : "rotate(-90deg)",
            }}
          >
            ▼
          </span>
        </div>
        {isScriptMediaExpanded && (
          <div className="animate-fadeIn">
            <div className="p-4 md:p-6 border-b border-gray-100">
              <h4 className="text-base font-medium text-primary mb-4">
                Script: {generatedContent.script.title}
              </h4>
              {generatedContent.script.scenes.map((scene) => (
                <div
                  key={scene.scene_number}
                  className="mb-4 pb-4 border-b border-gray-100 last:mb-0 last:pb-0 last:border-0"
                >
                  <div className="font-semibold text-primary mb-2">
                    Scene {scene.scene_number}
                  </div>
                  <div className="text-gray-700">{scene.script}</div>
                </div>
              ))}
            </div>

            <div className="p-4 md:p-6">
              <h4 className="text-base font-medium text-primary mb-4">Media</h4>

              {generatedContent.image_urls.length > 0 && (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                  {generatedContent.image_urls.map((url, index) => (
                    <div
                      key={index}
                      className="rounded overflow-hidden"
                    >
                      <img
                        src={`http://localhost:8000${url}`}
                        alt={`Scene ${index + 1}`}
                        className="w-full h-auto block"
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default VideoDetails
