import { Suspense } from 'react';
import FeedList from '../../components/FeedList';

export default function JobsPage() {
  return (
    <Suspense fallback={<div className="hn-loading">Loading...</div>}>
      <FeedList defaultSort="new" postType="job" />
    </Suspense>
  );
}
