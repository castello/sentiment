import { Table, Tag } from 'antd';

const LABEL_COLOR = { '긍정': 'green', '중립': 'orange', '부정': 'red' };

export default function SentenceTable({ sentences }) {
  const columns = [
    {
      title: '번호',
      key: 'index',
      width: 60,
      render: (_, __, idx) => idx + 1,
    },
    {
      title: '문장',
      dataIndex: 'sentence',
      ellipsis: true,
    },
    {
      title: '감성',
      dataIndex: 'label',
      width: 80,
      render: (label) => <Tag color={LABEL_COLOR[label]}>{label}</Tag>,
    },
    {
      title: '신뢰도',
      dataIndex: 'confidence',
      width: 90,
      render: (v) => v.toFixed(4),
    },
  ];

  return (
    <Table
      dataSource={sentences}
      columns={columns}
      rowKey={(_, idx) => idx}
      size="small"
      pagination={{ pageSize: 20, showSizeChanger: true }}
    />
  );
}
