import FeedList from '../../components/FeedList';

export default function JobsPage() {
  return <FeedList defaultSort="new" postType="job" />;
}
