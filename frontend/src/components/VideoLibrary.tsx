import React from "react"
import {
  formatFolderTitle,
  formatFolderDate,
  isRecentlyCreated,
} from "../utils/formatters"

interface VideoLibraryProps {
  folders: string[]
  selectedFolder: string
  currentPage: number
  itemsPerPage: number
  isLoading: boolean
  refreshing: boolean
  error: string | null
  getThumbnailForFolder: (folder: string) => string | null
  thumbnailsLoading: Record<string, boolean>
  folderHasVideo: (folder: string) => boolean
  handleFolderSelect: (folder: string) => Promise<any>
  handleThumbnailError: (folder: string) => void
  refreshFolders: () => Promise<void>
  setActiveTab: (tab: "library" | "details") => void
  setCurrentPage: (page: number | ((prev: number) => number)) => void
}

const VideoLibrary: React.FC<VideoLibraryProps> = ({
  folders,
  selectedFolder,
  currentPage,
  itemsPerPage,
  isLoading,
  refreshing,
  error,
  getThumbnailForFolder,
  thumbnailsLoading,
  folderHasVideo,
  handleFolderSelect,
  handleThumbnailError,
  refreshFolders,
  setActiveTab,
  setCurrentPage,
}) => {
  const totalPages = Math.ceil(folders.length / itemsPerPage)

  return (
    <>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-800">
          Generated Videos
        </h2>
        <button
          className={`bg-transparent border-none text-gray-500 hover:text-primary text-lg cursor-pointer transition-transform w-10 h-10 rounded-full flex items-center justify-center ${
            refreshing ? "spinning" : ""
          }`}
          onClick={refreshFolders}
          disabled={refreshing || isLoading}
          title="Refresh video library"
        >
          🔄
        </button>
      </div>

      {isLoading ? (
        <div className="flex flex-col justify-center items-center py-12 px-8 text-center">
          <div className="spinner"></div>
          <p className="mt-6 text-gray-600">Loading your videos...</p>
        </div>
      ) : folders.length > 0 ? (
        <div className="flex-1 flex flex-col">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {folders
              .slice(
                (currentPage - 1) * itemsPerPage,
                currentPage * itemsPerPage
              )
              .map((folder) => (
                <div
                  key={folder}
                  className={`generation-card ${
                    selectedFolder === folder ? "selected" : ""
                  }`}
                  onClick={() => {
                    handleFolderSelect(folder)
                    setActiveTab("details")
                  }}
                >
                  <div className="relative w-full pt-[56.25%] overflow-hidden">
                    {getThumbnailForFolder(folder) ? (
                      <video
                        src={getThumbnailForFolder(folder) || ""}
                        muted
                        playsInline
                        loop
                        preload="metadata"
                        onError={() => handleThumbnailError(folder)}
                        onMouseEnter={(e) => {
                          const video = e.currentTarget
                          video.currentTime = 0
                          video.play().catch(() => {})
                        }}
                        onMouseLeave={(e) => {
                          const video = e.currentTarget
                          video.pause()
                          video.currentTime = 0
                        }}
                        className="absolute top-0 left-0 w-full h-full object-cover"
                      />
                    ) : (
                      <div className="absolute top-0 left-0 w-full h-full flex items-center justify-center text-gray-400 text-5xl">
                        🎬
                      </div>
                    )}
                    {thumbnailsLoading[folder] && (
                      <div className="absolute inset-0 bg-black/10 flex items-center justify-center">
                        <div className="thumbnail-spinner"></div>
                      </div>
                    )}
                    {isRecentlyCreated(folder) && (
                      <div className="new-badge">NEW</div>
                    )}
                  </div>
                  <div className="p-4">
                    <div className="font-semibold mb-2 text-gray-800 whitespace-nowrap overflow-hidden text-ellipsis">
                      {formatFolderTitle(folder)}
                    </div>
                    <div className="text-sm text-gray-500">
                      {formatFolderDate(folder)}
                    </div>
                  </div>
                  <div
                    className={`absolute top-2 right-2 w-3 h-3 rounded-full ${
                      folderHasVideo(folder)
                        ? "status-complete"
                        : "status-processing"
                    }`}
                  ></div>
                </div>
              ))}
          </div>

          {/* Pagination Controls */}
          {folders.length > itemsPerPage && (
            <div className="flex justify-center items-center mt-8 gap-2">
              <button
                className="bg-gray-100 border border-gray-300 rounded px-3 py-2 cursor-pointer text-sm transition-all flex justify-center items-center min-w-10 disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
              >
                &laquo;
              </button>

              {/* Page number buttons */}
              <div className="flex gap-2">
                {Array.from(
                  {
                    length: Math.min(5, totalPages),
                  },
                  (_, i) => {
                    // Calculate which page numbers to show
                    let pageNum: number

                    if (totalPages <= 5) {
                      // If 5 or fewer pages, show all pages
                      pageNum = i + 1
                    } else if (currentPage <= 3) {
                      // If near the start, show pages 1-5
                      pageNum = i + 1
                    } else if (currentPage >= totalPages - 2) {
                      // If near the end, show the last 5 pages
                      pageNum = totalPages - 4 + i
                    } else {
                      // Otherwise show current page and 2 on each side
                      pageNum = currentPage - 2 + i
                    }

                    return (
                      <button
                        key={pageNum}
                        className={`bg-gray-100 border border-gray-300 rounded px-0 py-2 cursor-pointer text-sm transition-all flex justify-center items-center min-w-10 ${
                          currentPage === pageNum
                            ? "bg-primary text-white border-primary"
                            : ""
                        }`}
                        onClick={() => setCurrentPage(pageNum)}
                      >
                        {pageNum}
                      </button>
                    )
                  }
                )}
              </div>

              <button
                className="bg-gray-100 border border-gray-300 rounded px-3 py-2 cursor-pointer text-sm transition-all flex justify-center items-center min-w-10 disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={() =>
                  setCurrentPage((prev) => Math.min(prev + 1, totalPages))
                }
                disabled={currentPage >= totalPages}
              >
                &raquo;
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-16 px-8 bg-gray-50/80 rounded-lg text-gray-500">
          <div className="text-5xl mb-4 opacity-70">🎥</div>
          <h3 className="text-2xl mb-4 text-gray-800">No Videos Yet</h3>
          <p>Generate your first video by entering a prompt above.</p>
        </div>
      )}
    </>
  )
}

export default VideoLibrary
