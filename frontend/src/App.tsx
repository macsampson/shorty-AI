import React, { useState, useEffect } from "react"
import "./styles/tailwind.css"

// Import hooks
import { useFolders, useVideoGeneration } from "./hooks"

// Import components
import { Header, VideoForm, VideoLibrary, VideoDetails } from "./components"

// Import types
import { WindowSize } from "./types"

function App() {
  const {
    folders,
    selectedFolder,
    generatedContent,
    folderThumbnails,
    thumbnailsLoading,
    isLoading: foldersLoading,
    refreshing,
    error: folderError,
    currentPage,
    setCurrentPage,
    fetchFolders,
    refreshFolders,
    handleFolderSelect,
    getThumbnailForFolder,
    handleThumbnailError,
    setGeneratedContent,
    setSelectedFolder,
  } = useFolders()

  const {
    loading,
    videoGenerating,
    prompt,
    error: videoError,
    progress,
    currentStage,
    statusMessage,
    expandedPrompt,
    expanding,
    durationSeconds,
    setPrompt,
    setVideoGenerating,
    setDurationSeconds,
    handleSubmit,
    handleExpand,
  } = useVideoGeneration(selectedFolder, setGeneratedContent)

  // Active tab state
  const [activeTab, setActiveTab] = useState<"library" | "details">("library")

  // Window size state for responsive design
  const [windowSize, setWindowSize] = useState<WindowSize>({
    width: window.innerWidth,
    height: window.innerHeight,
  })

  // Determine items per page based on screen size
  const getItemsPerPage = () => {
    if (windowSize.width <= 480) return 4
    if (windowSize.width <= 768) return 6
    return 9
  }

  const itemsPerPage = getItemsPerPage()

  // Function to check if a folder has a video
  const folderHasVideo = (folder: string): boolean => {
    if (selectedFolder === folder) {
      return (
        !videoGenerating &&
        !!generatedContent &&
        !!generatedContent.video_urls &&
        generatedContent.video_urls.length > 0
      )
    }
    return true
  }

  // Handle successful video generation
  const handleVideoGenerated = async () => {
    const updatedFolders = await fetchFolders()

    if (updatedFolders && updatedFolders.length > 0) {
      handleFolderSelect(updatedFolders[0])
      setActiveTab("details")
    }
  }

  // Add resize event listener
  useEffect(() => {
    const handleResize = () => {
      const newSize = {
        width: window.innerWidth,
        height: window.innerHeight,
      }

      const oldItemsPerPage = getItemsPerPage()
      setWindowSize(newSize)
      const newItemsPerPage = getItemsPerPage()

      if (oldItemsPerPage !== newItemsPerPage && folders.length > 0) {
        const firstItemIndex = (currentPage - 1) * oldItemsPerPage
        const newPage = Math.floor(firstItemIndex / newItemsPerPage) + 1
        setCurrentPage(newPage)
      }
    }

    window.addEventListener("resize", handleResize)

    return () => {
      window.removeEventListener("resize", handleResize)
    }
  }, [currentPage, folders.length, setCurrentPage])

  // Wrap the handleSubmit to handle additional actions after successful generation
  const handleVideoSubmit = async (e: React.FormEvent) => {
    const success = await handleSubmit(e)
    if (success) {
      handleVideoGenerated()
    }
  }

  return (
    <div className="w-full min-h-full max-w-screen p-[2vh_2vw] box-border flex flex-col overflow-x-hidden bg-gray-50 text-gray-800">
      <Header />

      <div className="w-full max-w-7xl mx-auto flex flex-col gap-6 md:gap-8">
        <VideoForm
          prompt={prompt}
          setPrompt={setPrompt}
          handleSubmit={handleVideoSubmit}
          handleExpand={handleExpand}
          loading={loading}
          videoGenerating={videoGenerating}
          expanding={expanding}
          expandedPrompt={expandedPrompt}
          error={videoError}
          progress={progress}
          currentStage={currentStage}
          statusMessage={statusMessage}
          durationSeconds={durationSeconds}
          setDurationSeconds={setDurationSeconds}
        />

        <div className="w-full bg-white rounded-lg shadow-md p-4 md:p-6">
          <div className="flex border-b border-gray-200 mb-4">
            <div
              className={`px-4 py-2 cursor-pointer font-medium ${
                activeTab === "library"
                  ? "text-blue-600 border-b-2 border-blue-600"
                  : "text-gray-600 hover:text-gray-800"
              }`}
              onClick={() => {
                setActiveTab("library")
                setCurrentPage(1)
              }}
            >
              Video Library
            </div>
            {selectedFolder && (
              <div
                className={`px-4 py-2 cursor-pointer font-medium ${
                  activeTab === "details"
                    ? "text-blue-600 border-b-2 border-blue-600"
                    : "text-gray-600 hover:text-gray-800"
                }`}
                onClick={() => setActiveTab("details")}
              >
                Video Details
              </div>
            )}
          </div>

          {activeTab === "library" ? (
            <VideoLibrary
              folders={folders}
              selectedFolder={selectedFolder}
              currentPage={currentPage}
              itemsPerPage={itemsPerPage}
              isLoading={foldersLoading}
              refreshing={refreshing}
              error={folderError}
              getThumbnailForFolder={getThumbnailForFolder}
              thumbnailsLoading={thumbnailsLoading}
              folderHasVideo={folderHasVideo}
              handleFolderSelect={handleFolderSelect}
              handleThumbnailError={handleThumbnailError}
              refreshFolders={refreshFolders}
              setActiveTab={setActiveTab}
              setCurrentPage={setCurrentPage}
            />
          ) : (
            <VideoDetails
              selectedFolder={selectedFolder}
              generatedContent={generatedContent}
              videoGenerating={videoGenerating}
            />
          )}
        </div>

        <footer className="w-full text-center py-4 text-gray-500 text-sm mt-auto">
          <p>apparition.io</p>
        </footer>
      </div>
    </div>
  )
}

export default App
