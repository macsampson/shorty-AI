/**
 * Format folder title from folder name
 */
export const formatFolderTitle = (folder: string): string => {
  const parts = folder.split("_")
  if (parts.length >= 5) {
    return parts.slice(4).join(" ").replace(/_/g, " ")
  }
  return "Untitled Video"
}

/**
 * Format folder date from folder name
 */
export const formatFolderDate = (folder: string): string => {
  const parts = folder.split("_")
  const dateStr = parts.length >= 3 ? parts.slice(0, 3).join("-") : ""
  const timeStr =
    parts.length >= 4 && parts[3] ? parts[3].replace(/-/g, ":") : ""
  return `${dateStr} ${timeStr}`
}

/**
 * Check if a folder was created recently (within the last hour)
 */
export const isRecentlyCreated = (folder: string): boolean => {
  const parts = folder.split("_")
  if (parts.length < 4) return false

  // Extract date and time parts
  const year = parseInt(parts[0])
  const month = parseInt(parts[1]) - 1 // JavaScript months are 0-indexed
  const day = parseInt(parts[2])
  const timeParts = parts[3].split("-")

  if (timeParts.length < 3) return false

  const hour = parseInt(timeParts[0])
  const minute = parseInt(timeParts[1])
  const second = parseInt(timeParts[2])

  // Create date object from folder name
  const folderDate = new Date(year, month, day, hour, minute, second)
  const now = new Date()

  // Check if the folder was created within the last hour
  const diffMs = now.getTime() - folderDate.getTime()
  const diffHours = diffMs / (1000 * 60 * 60)

  return diffHours < 1
}
