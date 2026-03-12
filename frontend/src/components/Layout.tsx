import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useConversionStore } from '../store/conversionStore';

export default function Layout() {
  const navigate = useNavigate();
  const { jobs } = useConversionStore();
  const token = localStorage.getItem('token');

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  const pendingCount = jobs.filter(
    (j) => j.status === 'pending' || j.status === 'processing'
  ).length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center space-x-3">
              <span className="text-3xl">📄</span>
              <span className="text-xl font-bold text-gray-900">
                PDF Converter
              </span>
            </Link>

            {/* Navigation */}
            <nav className="flex items-center space-x-6">
              <Link
                to="/convert"
                className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
              >
                Конвертировать
              </Link>
              <Link
                to="/history"
                className="relative text-gray-600 hover:text-gray-900 font-medium transition-colors"
              >
                История
                {pendingCount > 0 && (
                  <span className="absolute -top-2 -right-4 bg-primary-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                    {pendingCount}
                  </span>
                )}
              </Link>
              {token ? (
                <>
                  <button
                    onClick={handleLogout}
                    className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                  >
                    Выйти
                  </button>
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                  >
                    Войти
                  </Link>
                  <Link to="/register" className="btn-primary">
                    Регистрация
                  </Link>
                </>
              )}
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-500 text-sm">
            <p>PDF Converter Bot — Быстрая конвертация PDF в различные форматы</p>
            <p className="mt-2">
              Поддерживаемые форматы: DOCX, XLSX, PPTX, PNG, JPEG, TXT, HTML, RTF
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
