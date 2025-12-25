import { Suspense } from 'react';
import FeedList from '../components/FeedList';

export default function Home() {
  return (
    <Suspense fallback={<div className="hn-loading">Loading...</div>}>
      <FeedList defaultSort="new" />
    </Suspense>
  );
}
