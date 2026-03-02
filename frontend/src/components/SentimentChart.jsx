import { Bar } from 'react-chartjs-2';
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

export default function SentimentChart({ ratios, counts }) {
  const data = {
    labels: ['긍정', '중립', '부정'],
    datasets: [
      {
        label: '비율 (%)',
        data: [ratios['긍정'], ratios['중립'], ratios['부정']],
        backgroundColor: [
          'rgba(82, 196, 26, 0.7)',
          'rgba(250, 173, 20, 0.7)',
          'rgba(245, 34, 45, 0.7)',
        ],
        borderRadius: 4,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx) => {
            const label = ctx.label;
            return `${ctx.raw.toFixed(1)}% (${counts[label]}문장)`;
          },
        },
      },
    },
    scales: {
      y: { beginAtZero: true, max: 100, ticks: { callback: (v) => `${v}%` } },
    },
  };

  return <Bar data={data} options={options} height={120} />;
}
