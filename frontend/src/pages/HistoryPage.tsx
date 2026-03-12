import { Link } from 'react-router-dom';
import { useConversionStore } from '../store/conversionStore';
import { FORMAT_ICONS } from '../api';

export default function HistoryPage() {
  const { jobs, removeJob } = useConversionStore();

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      processing: 'bg-blue-100 text-blue-800',
      done: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    };
    return styles[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      pending: 'Ожидает',
      processing: 'В процессе',
      done: 'Готово',
      failed: 'Ошибка',
    };
    return labels[status] || status;
  };

  if (jobs.length === 0) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <div className="text-5xl mb-4">📋</div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          История пуста
        </h2>
        <p className="text-gray-600 mb-6">
          У вас пока нет задач на конвертацию
        </p>
        <Link to="/convert" className="btn-primary">
          Начать конвертацию
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">История конвертаций</h1>
        <button
          onClick={() => {
            if (confirm('Очистить всю историю?')) {
              useConversionStore.getState().clearHistory();
            }
          }}
          className="text-red-600 hover:text-red-700 font-medium"
        >
          Очистить историю
        </button>
      </div>

      <div className="space-y-4">
        {jobs.map((job) => (
          <div
            key={job.job_id}
            className="card hover:shadow-lg transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="text-3xl">
                  {FORMAT_ICONS[job.target_format as keyof typeof FORMAT_ICONS]}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-900">
                      {job.filename}
                    </span>
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(
                        job.status
                      )}`}
                    >
                      {getStatusLabel(job.status)}
                    </span>
                  </div>
                  <div className="text-sm text-gray-500 mt-1">
                    <span className="uppercase">{job.target_format}</span>
                    {' • '}
                    {new Date(job.created_at).toLocaleString('ru-RU')}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                {job.status === 'done' && job.download_url && (
                  <a
                    href={job.download_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-primary text-sm px-4 py-2"
                  >
                    📥 Скачать
                  </a>
                )}
                {job.status === 'done' && (
                  <Link
                    to={`/status/${job.job_id}`}
                    className="btn-secondary text-sm px-4 py-2"
                  >
                    Статус
                  </Link>
                )}
                <button
                  onClick={() => removeJob(job.job_id)}
                  className="text-gray-400 hover:text-red-600 p-2"
                  title="Удалить из истории"
                >
                  🗑️
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
