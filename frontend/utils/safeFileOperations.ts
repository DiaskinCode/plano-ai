import * as FileSystem from 'expo-file-system';
import { Alert } from 'react-native';

/**
 * Safe File Operations Utility
 *
 * Provides wrapper functions for file operations with built-in:
 * - Error handling
 * - Directory existence checks
 * - File validation
 * - Size limits
 *
 * Usage:
 * import { safeWriteFile, safeReadFile, validateFileUri } from '@/utils/safeFileOperations';
 */

// Maximum file size: 10MB
const MAX_FILE_SIZE = 10 * 1024 * 1024;

/**
 * Validates that a file URI exists and is accessible
 * @param uri - File URI to validate
 * @returns File info if valid, null otherwise
 */
export const validateFileUri = async (uri: string): Promise<FileSystem.FileInfo | null> => {
  try {
    if (!uri) {
      console.error('validateFileUri: URI is empty');
      return null;
    }

    const fileInfo = await FileSystem.getInfoAsync(uri);

    if (!fileInfo.exists) {
      console.error('validateFileUri: File does not exist:', uri);
      return null;
    }

    return fileInfo;
  } catch (error) {
    console.error('validateFileUri: Error validating file URI:', error);
    return null;
  }
};

/**
 * Checks if a file size is within acceptable limits
 * @param uri - File URI to check
 * @param maxSize - Maximum allowed size in bytes (default: 10MB)
 * @returns true if within limits, false otherwise
 */
export const checkFileSize = async (
  uri: string,
  maxSize: number = MAX_FILE_SIZE
): Promise<boolean> => {
  try {
    const fileInfo = await FileSystem.getInfoAsync(uri);

    if (!fileInfo.exists) {
      console.error('checkFileSize: File does not exist:', uri);
      return false;
    }

    if (fileInfo.size && fileInfo.size > maxSize) {
      const sizeMB = (fileInfo.size / (1024 * 1024)).toFixed(2);
      const maxMB = (maxSize / (1024 * 1024)).toFixed(2);
      console.error(`checkFileSize: File too large: ${sizeMB}MB (max: ${maxMB}MB)`);
      return false;
    }

    if (fileInfo.size === 0) {
      console.error('checkFileSize: File is empty');
      return false;
    }

    return true;
  } catch (error) {
    console.error('checkFileSize: Error checking file size:', error);
    return false;
  }
};

/**
 * Ensures a directory exists, creates it if it doesn't
 * @param dirPath - Directory path to ensure exists
 * @returns true if directory exists or was created, false otherwise
 */
export const ensureDirectoryExists = async (dirPath: string): Promise<boolean> => {
  try {
    const dirInfo = await FileSystem.getInfoAsync(dirPath);

    if (!dirInfo.exists) {
      await FileSystem.makeDirectoryAsync(dirPath, { intermediates: true });
      console.log('ensureDirectoryExists: Created directory:', dirPath);
    }

    return true;
  } catch (error) {
    console.error('ensureDirectoryExists: Error ensuring directory exists:', error);
    return false;
  }
};

/**
 * Safely writes a string to a file with error handling and directory checks
 * @param filePath - Full file path (must use FileSystem.documentDirectory or cacheDirectory)
 * @param content - Content to write
 * @param encoding - Encoding to use (default: utf8)
 * @returns true if successful, false otherwise
 */
export const safeWriteFile = async (
  filePath: string,
  content: string,
  encoding: FileSystem.EncodingType = FileSystem.EncodingType.UTF8
): Promise<boolean> => {
  try {
    // Validate path uses correct directory constants
    if (!filePath.startsWith(FileSystem.documentDirectory || '') &&
        !filePath.startsWith(FileSystem.cacheDirectory || '')) {
      console.error('safeWriteFile: Invalid path. Must use FileSystem.documentDirectory or cacheDirectory');
      return false;
    }

    // Extract directory path
    const dirPath = filePath.substring(0, filePath.lastIndexOf('/'));

    // Ensure directory exists
    const dirExists = await ensureDirectoryExists(dirPath);
    if (!dirExists) {
      return false;
    }

    // Write the file
    await FileSystem.writeAsStringAsync(filePath, content, { encoding });
    console.log('safeWriteFile: Successfully wrote file:', filePath);
    return true;
  } catch (error) {
    console.error('safeWriteFile: Error writing file:', error);
    return false;
  }
};

/**
 * Safely reads a file with error handling
 * @param filePath - Full file path to read
 * @param encoding - Encoding to use (default: utf8)
 * @returns File content if successful, null otherwise
 */
export const safeReadFile = async (
  filePath: string,
  encoding: FileSystem.EncodingType = FileSystem.EncodingType.UTF8
): Promise<string | null> => {
  try {
    // Validate file exists
    const fileInfo = await validateFileUri(filePath);
    if (!fileInfo) {
      return null;
    }

    // Read the file
    const content = await FileSystem.readAsStringAsync(filePath, { encoding });
    console.log('safeReadFile: Successfully read file:', filePath);
    return content;
  } catch (error) {
    console.error('safeReadFile: Error reading file:', error);
    return null;
  }
};

/**
 * Safely deletes a file with error handling
 * @param filePath - Full file path to delete
 * @returns true if successful, false otherwise
 */
export const safeDeleteFile = async (filePath: string): Promise<boolean> => {
  try {
    // Check if file exists
    const fileInfo = await FileSystem.getInfoAsync(filePath);
    if (!fileInfo.exists) {
      console.log('safeDeleteFile: File does not exist:', filePath);
      return true; // Not an error if file doesn't exist
    }

    // Delete the file
    await FileSystem.deleteAsync(filePath);
    console.log('safeDeleteFile: Successfully deleted file:', filePath);
    return true;
  } catch (error) {
    console.error('safeDeleteFile: Error deleting file:', error);
    return false;
  }
};

/**
 * Safely copies a file with error handling and validation
 * @param sourceUri - Source file URI
 * @param destinationUri - Destination file URI (must use FileSystem.documentDirectory or cacheDirectory)
 * @returns true if successful, false otherwise
 */
export const safeCopyFile = async (
  sourceUri: string,
  destinationUri: string
): Promise<boolean> => {
  try {
    // Validate source file exists
    const sourceInfo = await validateFileUri(sourceUri);
    if (!sourceInfo) {
      return false;
    }

    // Validate destination path
    if (!destinationUri.startsWith(FileSystem.documentDirectory || '') &&
        !destinationUri.startsWith(FileSystem.cacheDirectory || '')) {
      console.error('safeCopyFile: Invalid destination. Must use FileSystem.documentDirectory or cacheDirectory');
      return false;
    }

    // Ensure destination directory exists
    const destDirPath = destinationUri.substring(0, destinationUri.lastIndexOf('/'));
    const dirExists = await ensureDirectoryExists(destDirPath);
    if (!dirExists) {
      return false;
    }

    // Copy the file
    await FileSystem.copyAsync({ from: sourceUri, to: destinationUri });
    console.log('safeCopyFile: Successfully copied file from', sourceUri, 'to', destinationUri);
    return true;
  } catch (error) {
    console.error('safeCopyFile: Error copying file:', error);
    return false;
  }
};

/**
 * Safely moves a file with error handling and validation
 * @param sourceUri - Source file URI
 * @param destinationUri - Destination file URI (must use FileSystem.documentDirectory or cacheDirectory)
 * @returns true if successful, false otherwise
 */
export const safeMoveFile = async (
  sourceUri: string,
  destinationUri: string
): Promise<boolean> => {
  try {
    // Validate source file exists
    const sourceInfo = await validateFileUri(sourceUri);
    if (!sourceInfo) {
      return false;
    }

    // Validate destination path
    if (!destinationUri.startsWith(FileSystem.documentDirectory || '') &&
        !destinationUri.startsWith(FileSystem.cacheDirectory || '')) {
      console.error('safeMoveFile: Invalid destination. Must use FileSystem.documentDirectory or cacheDirectory');
      return false;
    }

    // Ensure destination directory exists
    const destDirPath = destinationUri.substring(0, destinationUri.lastIndexOf('/'));
    const dirExists = await ensureDirectoryExists(destDirPath);
    if (!dirExists) {
      return false;
    }

    // Move the file
    await FileSystem.moveAsync({ from: sourceUri, to: destinationUri });
    console.log('safeMoveFile: Successfully moved file from', sourceUri, 'to', destinationUri);
    return true;
  } catch (error) {
    console.error('safeMoveFile: Error moving file:', error);
    return false;
  }
};

/**
 * Gets file information safely
 * @param uri - File URI
 * @returns File info object or null if error
 */
export const getFileInfo = async (uri: string): Promise<FileSystem.FileInfo | null> => {
  try {
    return await FileSystem.getInfoAsync(uri);
  } catch (error) {
    console.error('getFileInfo: Error getting file info:', error);
    return null;
  }
};

/**
 * Cleans up old files in a directory based on age
 * @param directoryUri - Directory to clean
 * @param maxAgeMs - Maximum age in milliseconds (default: 7 days)
 * @returns Number of files deleted
 */
export const cleanupOldFiles = async (
  directoryUri: string,
  maxAgeMs: number = 7 * 24 * 60 * 60 * 1000 // 7 days
): Promise<number> => {
  try {
    const dirInfo = await FileSystem.getInfoAsync(directoryUri);
    if (!dirInfo.exists) {
      return 0;
    }

    const files = await FileSystem.readDirectoryAsync(directoryUri);
    const now = Date.now();
    let deletedCount = 0;

    for (const file of files) {
      const filePath = `${directoryUri}/${file}`;
      const fileInfo = await FileSystem.getInfoAsync(filePath);

      if (fileInfo.exists && fileInfo.modificationTime) {
        const ageMs = now - (fileInfo.modificationTime * 1000);
        if (ageMs > maxAgeMs) {
          await FileSystem.deleteAsync(filePath);
          deletedCount++;
        }
      }
    }

    console.log(`cleanupOldFiles: Deleted ${deletedCount} old files from ${directoryUri}`);
    return deletedCount;
  } catch (error) {
    console.error('cleanupOldFiles: Error cleaning up old files:', error);
    return 0;
  }
};

/**
 * Gets the size of a directory and all its contents
 * @param directoryUri - Directory URI
 * @returns Total size in bytes, or 0 if error
 */
export const getDirectorySize = async (directoryUri: string): Promise<number> => {
  try {
    const dirInfo = await FileSystem.getInfoAsync(directoryUri);
    if (!dirInfo.exists) {
      return 0;
    }

    const files = await FileSystem.readDirectoryAsync(directoryUri);
    let totalSize = 0;

    for (const file of files) {
      const filePath = `${directoryUri}/${file}`;
      const fileInfo = await FileSystem.getInfoAsync(filePath);

      if (fileInfo.exists && fileInfo.size) {
        totalSize += fileInfo.size;
      }
    }

    return totalSize;
  } catch (error) {
    console.error('getDirectorySize: Error calculating directory size:', error);
    return 0;
  }
};

/**
 * Helper function to format file size for display
 * @param bytes - Size in bytes
 * @returns Formatted string (e.g., "1.5 MB")
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

export default {
  validateFileUri,
  checkFileSize,
  ensureDirectoryExists,
  safeWriteFile,
  safeReadFile,
  safeDeleteFile,
  safeCopyFile,
  safeMoveFile,
  getFileInfo,
  cleanupOldFiles,
  getDirectorySize,
  formatFileSize,
  MAX_FILE_SIZE,
};
