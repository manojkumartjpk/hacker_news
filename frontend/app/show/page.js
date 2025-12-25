import { Suspense } from 'react';
import FeedList from '../../components/FeedList';

export default function ShowPage() {
  return (
    <Suspense fallback={<div className="hn-loading">Loading...</div>}>
      <FeedList defaultSort="new" postType="show" />
    </Suspense>
  );
}
