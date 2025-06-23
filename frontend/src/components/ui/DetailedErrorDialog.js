import React from 'react';
import { Alert, AlertDescription } from '../ui/alert';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { AlertTriangle, Copy, ExternalLink, Info } from 'lucide-react';

const DetailedErrorDialog = ({ error, onClose, title = "Детали ошибки" }) => {
  const copyErrorToClipboard = () => {
    const errorText = JSON.stringify(error, null, 2);
    navigator.clipboard.writeText(errorText);
  };

  const renderErrorDetails = (errorData) => {
    if (typeof errorData === 'string') {
      return <pre className="text-sm bg-slate-100 dark:bg-slate-800 p-3 rounded overflow-auto">{errorData}</pre>;
    }

    if (typeof errorData === 'object' && errorData !== null) {
      return (
        <div className="space-y-3">
          {Object.entries(errorData).map(([key, value]) => (
            <div key={key} className="border-l-2 border-blue-500 pl-3">
              <div className="font-medium text-sm text-blue-600 dark:text-blue-400 capitalize">
                {key.replace(/_/g, ' ')}
              </div>
              <div className="mt-1">
                {Array.isArray(value) ? (
                  <ul className="list-disc list-inside space-y-1">
                    {value.map((item, index) => (
                      <li key={index} className="text-sm text-slate-600 dark:text-slate-400">
                        {item}
                      </li>
                    ))}
                  </ul>
                ) : typeof value === 'object' ? (
                  renderErrorDetails(value)
                ) : (
                  <div className="text-sm text-slate-700 dark:text-slate-300">
                    {String(value)}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      );
    }

    return <div className="text-sm">{String(errorData)}</div>;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-4xl max-h-[90vh] overflow-auto">
        <CardHeader>
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-red-500" />
            <CardTitle className="text-red-600 dark:text-red-400">{title}</CardTitle>
          </div>
          <CardDescription>
            Подробная информация об ошибке для диагностики проблемы
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Основное сообщение об ошибке */}
          {error.message && (
            <Alert variant="destructive">
              <AlertDescription className="font-medium">
                {error.message}
              </AlertDescription>
            </Alert>
          )}

          {/* HTTP статус, если есть */}
          {error.status && (
            <div className="flex items-center space-x-2">
              <Badge variant="destructive">HTTP {error.status}</Badge>
              <span className="text-sm text-slate-600 dark:text-slate-400">
                {error.statusText || "Unknown Error"}
              </span>
            </div>
          )}

          {/* Детали ошибки */}
          {error.data && (
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Info className="w-4 h-4 text-blue-500" />
                <h4 className="font-medium">Технические детали:</h4>
              </div>
              {renderErrorDetails(error.data)}
            </div>
          )}

          {/* Предложения по устранению */}
          {error.data?.troubleshooting && (
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <ExternalLink className="w-4 h-4 text-green-500" />
                <h4 className="font-medium text-green-600 dark:text-green-400">
                  Рекомендации по устранению:
                </h4>
              </div>
              <ul className="list-disc list-inside space-y-1 bg-green-50 dark:bg-green-900/20 p-3 rounded">
                {error.data.troubleshooting.map((suggestion, index) => (
                  <li key={index} className="text-sm text-green-700 dark:text-green-300">
                    {suggestion}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Параметры подключения */}
          {error.data?.connection_attempt && (
            <div className="space-y-3">
              <h4 className="font-medium">Параметры подключения:</h4>
              <div className="bg-slate-50 dark:bg-slate-800 p-3 rounded">
                <pre className="text-sm">
                  {JSON.stringify(error.data.connection_attempt, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Стек ошибки для разработчиков */}
          {error.stack && (
            <details className="group">
              <summary className="cursor-pointer font-medium text-slate-600 dark:text-slate-400 group-open:text-slate-800 dark:group-open:text-slate-200">
                Стек вызовов (для разработчиков)
              </summary>
              <pre className="mt-2 text-xs bg-slate-100 dark:bg-slate-800 p-3 rounded overflow-auto">
                {error.stack}
              </pre>
            </details>
          )}

          {/* Действия */}
          <div className="flex space-x-2 pt-4">
            <Button onClick={onClose} className="flex-1">
              Закрыть
            </Button>
            <Button variant="outline" onClick={copyErrorToClipboard}>
              <Copy className="w-4 h-4 mr-2" />
              Копировать
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DetailedErrorDialog;