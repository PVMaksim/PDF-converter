import { Link } from 'react-router-dom';
import { FORMAT_ICONS, FORMAT_LABELS, type SupportedFormat } from '../api';

const FORMATS: SupportedFormat[] = [
  'docx',
  'xlsx',
  'pptx',
  'png',
  'jpeg',
  'txt',
  'html',
  'rtf',
];

export default function HomePage() {
  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="text-center py-12">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">
          Конвертация PDF файлов
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          Быстро и безопасно конвертируйте PDF в DOCX, XLSX, PPTX, PNG и другие
          форматы прямо в браузере
        </p>
        <div className="flex justify-center gap-4">
          <Link to="/convert" className="btn-primary text-lg px-8 py-4">
            Начать конвертацию
          </Link>
          <Link to="/history" className="btn-secondary text-lg px-8 py-4">
            История конвертаций
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="grid md:grid-cols-3 gap-6">
        <div className="card text-center">
          <div className="text-4xl mb-4">⚡</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Быстрая обработка
          </h3>
          <p className="text-gray-600">
            Конвертация файлов за считанные секунды благодаря асинхронной
            обработке
          </p>
        </div>
        <div className="card text-center">
          <div className="text-4xl mb-4">🔒</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Безопасность
          </h3>
          <p className="text-gray-600">
            Файлы автоматически удаляются через 24 часа. Никакого постоянного
            хранения
          </p>
        </div>
        <div className="card text-center">
          <div className="text-4xl mb-4">📱</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Удобный доступ
          </h3>
          <p className="text-gray-600">
            Работайте через веб-интерфейс или Telegram бота в любое время
          </p>
        </div>
      </section>

      {/* Supported Formats */}
      <section>
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-8">
          Поддерживаемые форматы
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {FORMATS.map((format) => (
            <div
              key={format}
              className="card hover:shadow-xl transition-shadow cursor-pointer"
            >
              <div className="text-3xl mb-2">{FORMAT_ICONS[format]}</div>
              <div className="font-semibold text-gray-900 uppercase">
                {format}
              </div>
              <div className="text-sm text-gray-500">
                {FORMAT_LABELS[format]}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section className="bg-white rounded-xl shadow-lg p-8">
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-8">
          Как это работает
        </h2>
        <div className="grid md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="w-12 h-12 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">
              1
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Загрузите PDF</h3>
            <p className="text-gray-600 text-sm">
              Перетащите файл или выберите через диалог
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">
              2
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">
              Выберите формат
            </h3>
            <p className="text-gray-600 text-sm">
              DOCX, XLSX, PNG или другой формат
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">
              3
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">
              Дождитесь обработки
            </h3>
            <p className="text-gray-600 text-sm">
              Отслеживайте прогресс в реальном времени
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">
              4
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Скачайте файл</h3>
            <p className="text-gray-600 text-sm">
              Получите готовый файл одним кликом
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
