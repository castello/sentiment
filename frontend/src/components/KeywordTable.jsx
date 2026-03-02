import { Table } from 'antd';

export default function KeywordTable({ data, valueKey, valueTitle }) {
  const columns = [
    {
      title: '순위',
      key: 'rank',
      width: 60,
      render: (_, __, idx) => idx + 1,
    },
    {
      title: '키워드',
      dataIndex: 'keyword',
    },
    {
      title: valueTitle,
      dataIndex: valueKey,
      width: 100,
    },
  ];

  return (
    <Table
      dataSource={data}
      columns={columns}
      rowKey="keyword"
      size="small"
      pagination={false}
    />
  );
}
