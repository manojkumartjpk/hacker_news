import { Suspense } from 'react';
import SearchPageClient from '../../components/SearchPageClient';

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="hn-loading">Loading...</div>}>
      <SearchPageClient />
    </Suspense>
  );
}
