import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import { filesAPI, conversionsAPI, type SupportedFormat } from '../api';
import { useConversionStore } from '../store/conversionStore';
import FileUpload from '../components/FileUpload';
import FormatSelector from '../components/FormatSelector';

export default function ConvertPage() {
  const navigate = useNavigate();
  const { addJob, setCurrentJob } = useConversionStore();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFormat, setSelectedFormat] = useState<SupportedFormat | null>(
    null
  );

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: filesAPI.upload,
    onSuccess: (data) => {
      toast.success('Файл успешно загружен!');
      return data.data;
    },
    onError: (error: any) => {
      toast.error(
        error.response?.data?.detail || 'Ошибка при загрузке файла'
      );
    },
  });

  // Convert mutation
  const convertMutation = useMutation({
    mutationFn: conversionsAPI.create,
    onSuccess: (data) => {
      const job = data.data;
      addJob({
        job_id: job.job_id,
        file_id: uploadMutation.data?.file_id || '',
        filename: selectedFile?.name || '',
        target_format: job.target_format,
        download_url: '',
      });
      setCurrentJob({
        job_id: job.job_id,
        file_id: uploadMutation.data?.file_id || '',
        filename: selectedFile?.name || '',
        target_format: job.target_format,
        status: job.status,
        created_at: new Date().toISOString(),
        download_url: '',
      });
      toast.success('Конвертация началась!');
      navigate(`/status/${job.job_id}`);
    },
    onError: (error: any) => {
      toast.error(
        error.response?.data?.detail || 'Ошибка при создании задачи'
      );
    },
  });

  const handleFileSelect = useCallback((file: File) => {
    setSelectedFile(file);
    setSelectedFormat(null);
  }, []);

  const handleFormatSelect = (format: SupportedFormat) => {
    setSelectedFormat(format);
  };

  const handleConvert = async () => {
    if (!selectedFile || !selectedFormat) return;

    try {
      // Upload file
      const uploadResult = await uploadMutation.mutateAsync(selectedFile);

      // Create conversion job
      await convertMutation.mutateAsync({
        file_id: uploadResult.file_id,
        target_format: selectedFormat,
      });
    } catch (error) {
      console.error('Conversion error:', error);
    }
  };

  const isReady = selectedFile && selectedFormat && !convertMutation.isPending;

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Конвертация PDF
        </h1>
        <p className="text-gray-600">
          Загрузите PDF файл и выберите формат для конвертации
        </p>
      </div>

      {/* File Upload */}
      <FileUpload
        selectedFile={selectedFile}
        onFileSelect={handleFileSelect}
        disabled={convertMutation.isPending}
      />

      {/* Format Selector */}
      {selectedFile && (
        <FormatSelector
          selectedFormat={selectedFormat}
          onSelect={handleFormatSelect}
          disabled={convertMutation.isPending}
        />
      )}

      {/* Convert Button */}
      {selectedFormat && (
        <div className="flex justify-center">
          <button
            onClick={handleConvert}
            disabled={!isReady}
            className="btn-primary text-lg px-12 py-4"
          >
            {convertMutation.isPending ? (
              <span className="flex items-center gap-2">
                <svg
                  className="animate-spin h-5 w-5"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Обработка...
              </span>
            ) : (
              'Конвертировать'
            )}
          </button>
        </div>
      )}
    </div>
  );
}
