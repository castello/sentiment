import { useEffect, useMemo, useState } from 'react';
import { Button, DatePicker, Input, Select, Space, Table, message } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { fetchNews } from '../api/client';

const COUNT_OPTIONS = [
  { value: 5, label: '5' },
  { value: 10, label: '10' },
  { value: 20, label: '20' },
  { value: 50, label: '50' },
  { value: 100, label: '100' },
];

export default function NewsList({ onAnalyze, loading }) {
  const [newsList, setNewsList] = useState([]);
  const [fetching, setFetching] = useState(false);
  const [count, setCount] = useState(50);
  const [search, setSearch] = useState('');
  const [sourceFilter, setSourceFilter] = useState(null);
  const [dateRange, setDateRange] = useState(null);

  const loadNews = async (n) => {
    setFetching(true);
    try {
      const data = await fetchNews(n);
      setNewsList(data);
    } catch (err) {
      message.error('뉴스를 불러오지 못했습니다.');
    } finally {
      setFetching(false);
    }
  };

  useEffect(() => {
    loadNews(count);
  }, [count]);

  const sources = useMemo(() => {
    const set = new Set(newsList.map((n) => n.source).filter(Boolean));
    return [...set].sort();
  }, [newsList]);

  const filtered = useMemo(() => {
    let list = newsList;
    if (search) {
      const q = search.toLowerCase();
      list = list.filter((n) => n.title.toLowerCase().includes(q));
    }
    if (sourceFilter) {
      list = list.filter((n) => n.source === sourceFilter);
    }
    if (dateRange && dateRange[0] && dateRange[1]) {
      const from = dateRange[0].startOf('day');
      const to = dateRange[1].endOf('day');
      list = list.filter((n) => {
        if (!n.published) return false;
        const d = dayjs(n.published);
        return d.isAfter(from) && d.isBefore(to);
      });
    }
    return list;
  }, [newsList, search, sourceFilter, dateRange]);

  const columns = [
    {
      title: '번호',
      key: 'index',
      width: 70,
      render: (_, __, idx) => idx + 1,
    },
    {
      title: '제목',
      dataIndex: 'title',
      ellipsis: true,
    },
    {
      title: '언론사',
      dataIndex: 'source',
      width: 150,
    },
    {
      title: '발행시간',
      dataIndex: 'published',
      width: 160,
    },
    {
      title: '',
      key: 'action',
      width: 80,
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          loading={loading}
          onClick={() => onAnalyze(record.url)}
        >
          분석
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Space wrap style={{ marginBottom: 16 }}>
        <Select
          value={count}
          onChange={setCount}
          options={COUNT_OPTIONS}
          style={{ width: 80 }}
        />
        <Input
          placeholder="제목 검색"
          prefix={<SearchOutlined />}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
          style={{ width: 240 }}
        />
        <Select
          placeholder="언론사"
          value={sourceFilter}
          onChange={setSourceFilter}
          options={sources.map((s) => ({ value: s, label: s }))}
          allowClear
          style={{ width: 160 }}
        />
        <DatePicker.RangePicker
          value={dateRange}
          onChange={setDateRange}
        />
      </Space>
      <Table
        dataSource={filtered}
        columns={columns}
        rowKey={(r) => r.url}
        loading={fetching}
        size="middle"
        pagination={{ pageSize: 10, showSizeChanger: false }}
      />
    </div>
  );
}
