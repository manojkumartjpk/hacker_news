import { Suspense } from 'react';
import CommentsPageClient from '../../components/CommentsPageClient';

export default function CommentsPage() {
  return (
    <Suspense fallback={<div className="hn-loading">Loading...</div>}>
      <CommentsPageClient />
    </Suspense>
  );
}
