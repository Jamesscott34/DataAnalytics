import { useState } from 'react';

/**
 * TimeSeriesForm
 */
export function TimeSeriesForm({
  algorithms,
  columns,
  suggestions,
  loading,
  onSubmit,
}) {
  const dateColumns = suggestions?.date_columns?.length
    ? suggestions.date_columns
    : columns;
  const numericColumns = suggestions?.target_columns?.length
    ? suggestions.target_columns
    : columns;

  const defaultDate = dateColumns[0] ?? '';
  const defaultValue = numericColumns.find((column) => column !== defaultDate) ?? numericColumns[0] ?? '';
  const [algorithm, setAlgorithm] = useState(algorithms[0]?.id ?? 'moving_average');

  return (
    <form
      className="regression-form"
      onSubmit={(event) => {
        event.preventDefault();
        const formData = new FormData(event.currentTarget);
        onSubmit({
          algorithm: formData.get('algorithm'),
          dateColumn: formData.get('date_column'),
          valueColumn: formData.get('value_column'),
          forecastPeriods: Number(formData.get('forecast_periods')),
          window: Number(formData.get('window')),
          arLags: Number(formData.get('ar_lags')),
          arimaP: Number(formData.get('arima_p')),
          arimaD: Number(formData.get('arima_d')),
          arimaQ: Number(formData.get('arima_q')),
          seasonalPeriod: formData.get('seasonal_period')
            ? Number(formData.get('seasonal_period'))
            : null,
        });
      }}
    >
      <label htmlFor="timeseries-algorithm">Algorithm</label>
      <select
        id="timeseries-algorithm"
        name="algorithm"
        value={algorithm}
        onChange={(event) => setAlgorithm(event.target.value)}
        required
      >
        {algorithms.map((item) => (
          <option key={item.id} value={item.id}>
            {item.label}
          </option>
        ))}
      </select>

      <label htmlFor="timeseries-date">Date column</label>
      <select
        id="timeseries-date"
        name="date_column"
        defaultValue={defaultDate}
        required
      >
        {columns.map((column) => (
          <option key={column} value={column}>
            {column}
          </option>
        ))}
      </select>

      <label htmlFor="timeseries-value">Value column</label>
      <select
        id="timeseries-value"
        name="value_column"
        defaultValue={defaultValue}
        required
      >
        {columns.map((column) => (
          <option key={column} value={column}>
            {column}
          </option>
        ))}
      </select>

      <label htmlFor="timeseries-periods">Forecast periods</label>
      <input
        id="timeseries-periods"
        name="forecast_periods"
        type="number"
        min="1"
        max="30"
        defaultValue="5"
      />

      {algorithm === 'moving_average' && (
        <>
          <label htmlFor="timeseries-window">Moving average window</label>
          <input id="timeseries-window" name="window" type="number" min="2" max="30" defaultValue="3" />
        </>
      )}

      {algorithm === 'autoregressive' && (
        <>
          <label htmlFor="timeseries-ar-lags">AR lags</label>
          <input id="timeseries-ar-lags" name="ar_lags" type="number" min="1" max="20" defaultValue="3" />
        </>
      )}

      {algorithm === 'arima' && (
        <>
          <label htmlFor="timeseries-arima-p">ARIMA p</label>
          <input id="timeseries-arima-p" name="arima_p" type="number" min="0" max="5" defaultValue="1" />
          <label htmlFor="timeseries-arima-d">ARIMA d</label>
          <input id="timeseries-arima-d" name="arima_d" type="number" min="0" max="2" defaultValue="1" />
          <label htmlFor="timeseries-arima-q">ARIMA q</label>
          <input id="timeseries-arima-q" name="arima_q" type="number" min="0" max="5" defaultValue="1" />
        </>
      )}

      {algorithm === 'sarimax' && (
        <>
          <label htmlFor="timeseries-seasonal">Seasonal period</label>
          <input
            id="timeseries-seasonal"
            name="seasonal_period"
            type="number"
            min="2"
            max="365"
            defaultValue="12"
            required
          />
          <label htmlFor="timeseries-sarimax-p">ARIMA p</label>
          <input id="timeseries-sarimax-p" name="arima_p" type="number" min="0" max="5" defaultValue="1" />
          <label htmlFor="timeseries-sarimax-d">ARIMA d</label>
          <input id="timeseries-sarimax-d" name="arima_d" type="number" min="0" max="2" defaultValue="1" />
          <label htmlFor="timeseries-sarimax-q">ARIMA q</label>
          <input id="timeseries-sarimax-q" name="arima_q" type="number" min="0" max="5" defaultValue="1" />
        </>
      )}

      <button type="submit" className="primary-button" disabled={loading || columns.length === 0}>
        {loading ? 'Forecasting…' : 'Run forecast'}
      </button>
    </form>
  );
}
