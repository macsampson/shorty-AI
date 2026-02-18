import { useState, useEffect } from "react"
import axios from "axios"
import { GeneratedContent } from "../types"

export const useFolders = () => {
  const [folders, setFolders] = useState<string[]>([])
  const [selectedFolder, setSelectedFolder] = useState<string>("")
  const [generatedContent, setGeneratedContent] =
    useState<GeneratedContent | null>(null)
  const [folderThumbnails, setFolderThumbnails] = useState<
    Record<string, string>
  >({})
  const [thumbnailsLoading, setThumbnailsLoading] = useState<
    Record<string, boolean>
  >({})
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [refreshing, setRefreshing] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState<number>(1)

  useEffect(() => {
    fetchFolders()
  }, [])

  const fetchFolders = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await axios.get(
        "http://localhost:8000/list_generated_content",
        { timeout: 5000 }
      )

      const sortedFolders = response.data.folders.sort(
        (a: string, b: string) => {
          return b.localeCompare(a) // Sort in descending order (newest first)
        }
      )

      setFolders(sortedFolders)

      // Reset to first page when folders are updated
      setCurrentPage(1)

      // Fetch thumbnails for all folders
      fetchThumbnailsForFolders(sortedFolders)

      return sortedFolders
    } catch (error) {
      console.error("Error fetching folders:", error)
      setError("Failed to fetch generated content.")
      return []
    } finally {
      setIsLoading(false)
    }
  }

  const refreshFolders = async () => {
    if (refreshing) return

    setRefreshing(true)
    try {
      await fetchFolders()
    } finally {
      // Add a small delay to make the refresh animation visible
      setTimeout(() => {
        setRefreshing(false)
      }, 500)
    }
  }

  const fetchThumbnailsForFolders = async (foldersList: string[]) => {
    const thumbnails: Record<string, string> = {}
    const loadingState: Record<string, boolean> = {}

    // Initialize loading state for all folders
    foldersList.forEach((folder) => {
      loadingState[folder] = true
    })
    setThumbnailsLoading(loadingState)

    // Process folders in batches to avoid overwhelming the server
    const batchSize = 5
    const batches = []

    // Split folders into batches
    for (let i = 0; i < foldersList.length; i += batchSize) {
      batches.push(foldersList.slice(i, i + batchSize))
    }

    // Process each batch sequentially
    for (const batch of batches) {
      // Create an array of promises for parallel fetching within the batch
      const batchPromises = batch.map(async (folder) => {
        try {
          const response = await axios.get(
            `http://localhost:8000/get_generated_content/${folder}`,
            { timeout: 5000 }
          )

          if (response.data.video_urls && response.data.video_urls.length > 0) {
            thumbnails[
              folder
            ] = `http://localhost:8000${response.data.video_urls[0]}`

            // Update thumbnails state incrementally as they load
            setFolderThumbnails((prev) => ({
              ...prev,
              [folder]: thumbnails[folder],
            }))
          }
        } catch (error) {
          console.error(`Error fetching thumbnail for folder ${folder}:`, error)
        } finally {
          // Update loading state for this folder
          setThumbnailsLoading((prev) => ({
            ...prev,
            [folder]: false,
          }))
        }
      })

      // Wait for all promises in this batch to complete before moving to the next batch
      await Promise.all(batchPromises)
    }
  }

  const handleFolderSelect = async (folder: string) => {
    setSelectedFolder(folder)

    try {
      const response = await axios.get(
        `http://localhost:8000/get_generated_content/${folder}`
      )

      setGeneratedContent(response.data)

      // If we have videos, update the thumbnail cache
      if (response.data.video_urls && response.data.video_urls.length > 0) {
        setFolderThumbnails((prev) => ({
          ...prev,
          [folder]: `http://localhost:8000${response.data.video_urls[0]}`,
        }))
      }

      return response.data
    } catch (error) {
      console.error("Error fetching folder content:", error)
      setError("Failed to fetch folder content.")
      return null
    }
  }

  const getThumbnailForFolder = (folder: string) => {
    // First check if we have a cached thumbnail
    if (folderThumbnails[folder]) {
      return folderThumbnails[folder]
    }

    // If this is the selected folder and we have content, use the first video
    if (
      selectedFolder === folder &&
      generatedContent &&
      generatedContent.video_urls.length > 0
    ) {
      const thumbnailUrl = `http://localhost:8000${generatedContent.video_urls[0]}`

      // Cache this thumbnail for future use
      setFolderThumbnails((prev) => ({
        ...prev,
        [folder]: thumbnailUrl,
      }))

      return thumbnailUrl
    }

    // Otherwise, return null to show placeholder
    return null
  }

  const handleThumbnailError = (folder: string) => {
    // Mark this folder as not loading anymore
    setThumbnailsLoading((prev) => ({
      ...prev,
      [folder]: false,
    }))

    // Remove the thumbnail from the cache so we show the placeholder instead
    setFolderThumbnails((prev) => {
      const newThumbnails = { ...prev }
      delete newThumbnails[folder]
      return newThumbnails
    })
  }

  return {
    folders,
    selectedFolder,
    generatedContent,
    folderThumbnails,
    thumbnailsLoading,
    isLoading,
    refreshing,
    error,
    currentPage,
    setCurrentPage,
    fetchFolders,
    refreshFolders,
    handleFolderSelect,
    getThumbnailForFolder,
    handleThumbnailError,
    setSelectedFolder,
    setGeneratedContent,
  }
}
