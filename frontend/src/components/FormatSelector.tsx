import { FORMAT_ICONS, FORMAT_LABELS, type SupportedFormat } from '../api';
import { clsx } from 'clsx';

const FORMATS: SupportedFormat[] = [
  'docx',
  'xlsx',
  'pptx',
  'rtf',
  'html',
  'png',
  'jpeg',
  'txt',
];

interface FormatSelectorProps {
  selectedFormat: SupportedFormat | null;
  onSelect: (format: SupportedFormat) => void;
  disabled?: boolean;
}

export default function FormatSelector({
  selectedFormat,
  onSelect,
  disabled = false,
}: FormatSelectorProps) {
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-gray-900 text-center">
        Выберите формат для конвертации
      </h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {FORMATS.map((format) => (
          <button
            key={format}
            onClick={() => onSelect(format)}
            disabled={disabled}
            className={clsx(
              'card p-4 transition-all duration-200',
              'hover:shadow-xl hover:scale-105',
              selectedFormat === format &&
                'ring-2 ring-primary-500 bg-primary-50',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
          >
            <div className="text-center">
              <div className="text-3xl mb-2">{FORMAT_ICONS[format]}</div>
              <div className="font-semibold text-gray-900 uppercase text-sm">
                {format}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {FORMAT_LABELS[format]}
              </div>
            </div>
          </button>
        ))}
      </div>

      {selectedFormat && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <span className="text-xl">✅</span>
            <div className="text-sm text-green-800">
              <p>
                Выбран формат:{' '}
                <span className="font-semibold uppercase">
                  {selectedFormat}
                </span>
              </p>
              <p className="text-gray-600">
                {FORMAT_LABELS[selectedFormat]}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
