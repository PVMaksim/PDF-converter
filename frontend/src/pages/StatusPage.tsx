import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { conversionsAPI, filesAPI } from '../api';
import { useConversionStore } from '../store/conversionStore';

export default function StatusPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const { updateJob } = useConversionStore();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['conversion', jobId],
    queryFn: () => conversionsAPI.getStatus(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.data.status;
      return status === 'done' || status === 'failed' ? false : 2000;
    },
  });

  useEffect(() => {
    if (data?.data) {
      const job = data.data;
      updateJob(job.job_id, {
        status: job.status,
        completed_at: job.completed_at || undefined,
        error_message: job.error_message || undefined,
      });
    }
  }, [data, updateJob]);

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <div className="animate-spin h-12 w-12 border-4 border-primary-500 border-t-transparent rounded-full mx-auto mb-4" />
        <p className="text-gray-600">Загрузка статуса...</p>
      </div>
    );
  }

  if (error || !data?.data) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <div className="text-5xl mb-4">❌</div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Ошибка загрузки
        </h2>
        <p className="text-gray-600 mb-6">
          Не удалось загрузить статус конвертации
        </p>
        <button onClick={() => navigate('/convert')} className="btn-primary">
          Вернуться к конвертации
        </button>
      </div>
    );
  }

  const job = data.data;
  const isDone = job.status === 'done';
  const isFailed = job.status === 'failed';
  const isProcessing = job.status === 'processing' || job.status === 'pending';

  const handleDownload = async () => {
    if (!job.result_file_id) return;

    try {
      const response = await filesAPI.download(job.result_file_id);
      window.open(response.data.download_url, '_blank');
      toast.success('Скачивание началось!');
    } catch (error) {
      toast.error('Ошибка при скачивании');
    }
  };

  const getStatusInfo = () => {
    switch (job.status) {
      case 'pending':
        return {
          icon: '⏳',
          title: 'В очереди',
          description: 'Задача ожидает обработки',
          color: 'text-yellow-600',
        };
      case 'processing':
        return {
          icon: '⚙️',
          title: 'Обработка',
          description: 'Файл конвертируется',
          color: 'text-blue-600',
        };
      case 'done':
        return {
          icon: '✅',
          title: 'Готово!',
          description: 'Файл готов к скачиванию',
          color: 'text-green-600',
        };
      case 'failed':
        return {
          icon: '❌',
          title: 'Ошибка',
          description: job.error_message || 'Неизвестная ошибка',
          color: 'text-red-600',
        };
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="card text-center py-8">
        <div className="text-6xl mb-4">{statusInfo.icon}</div>
        <h1 className={`text-2xl font-bold ${statusInfo.color} mb-2`}>
          {statusInfo.title}
        </h1>
        <p className="text-gray-600">{statusInfo.description}</p>
      </div>

      {/* Job Details */}
      <div className="card space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-gray-600">ID задачи:</span>
          <code className="text-sm bg-gray-100 px-2 py-1 rounded">
            {job.job_id}
          </code>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Формат:</span>
          <span className="font-semibold uppercase">
            PDF → {job.target_format}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Создана:</span>
          <span>
            {new Date(job.created_at).toLocaleString('ru-RU')}
          </span>
        </div>
        {job.completed_at && (
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Завершена:</span>
            <span>
              {new Date(job.completed_at).toLocaleString('ru-RU')}
            </span>
          </div>
        )}
      </div>

      {/* Actions */}
      {isDone && (
        <div className="flex justify-center gap-4">
          <button onClick={handleDownload} className="btn-primary text-lg px-8">
            📥 Скачать файл
          </button>
          <button
            onClick={() => navigate('/convert')}
            className="btn-secondary text-lg px-8"
          >
            Конвертировать ещё
          </button>
        </div>
      )}

      {isFailed && (
        <div className="flex justify-center gap-4">
          <button
            onClick={() => navigate('/convert')}
            className="btn-primary text-lg px-8"
          >
            Попробовать снова
          </button>
        </div>
      )}

      {isProcessing && (
        <div className="text-center">
          <div className="animate-pulse text-gray-600">
            Пожалуйста, дождитесь завершения обработки...
          </div>
          <button
            onClick={() => refetch()}
            className="btn-secondary mt-4"
          >
            Обновить статус
          </button>
        </div>
      )}
    </div>
  );
}
