import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { clsx } from 'clsx';

interface FileUploadProps {
  selectedFile: File | null;
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export default function FileUpload({
  selectedFile,
  onFileSelect,
  disabled = false,
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0 && !disabled) {
        onFileSelect(acceptedFiles[0]);
      }
    },
    [onFileSelect, disabled]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024, // 50 MB
    disabled,
  });

  const handleDragEnter = () => setIsDragging(true);
  const handleDragLeave = () => setIsDragging(false);
  const handleDrop = () => setIsDragging(false);

  const handleRemoveFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    // Dispatch custom event to clear file
    window.dispatchEvent(new CustomEvent('clear-file'));
  };

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={clsx(
          'card border-2 border-dashed transition-all duration-200 cursor-pointer',
          'hover:border-primary-400 hover:bg-primary-50',
          isDragActive && 'border-primary-500 bg-primary-100',
          isDragging && 'scale-105',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input {...getInputProps()} />
        <div className="text-center py-12 px-4">
          {selectedFile ? (
            <div className="space-y-4">
              <div className="text-5xl">📎</div>
              <div>
                <p className="text-lg font-semibold text-gray-900">
                  {selectedFile.name}
                </p>
                <p className="text-sm text-gray-500">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <button
                onClick={handleRemoveFile}
                className="text-red-600 hover:text-red-700 font-medium"
                type="button"
              >
                Удалить файл
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-5xl">📤</div>
              <div>
                <p className="text-lg font-medium text-gray-900">
                  {isDragActive
                    ? 'Перетащите файл сюда...'
                    : 'Перетащите PDF файл или нажмите для выбора'}
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  Максимальный размер: 50 MB
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <span className="text-xl">ℹ️</span>
          <div className="text-sm text-blue-800">
            <p className="font-semibold mb-1">Поддерживаются только PDF файлы</p>
            <p>
              Убедитесь, что ваш файл имеет расширение .pdf перед загрузкой
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
