'use client';

import { useState, useEffect } from 'react';
import PostItem from '../components/PostItem';
import { postsAPI } from '../lib/api';

export default function Home() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sort, setSort] = useState('new');

  useEffect(() => {
    fetchPosts();
  }, [sort]);

  const fetchPosts = async () => {
    try {
      setLoading(true);
      const response = await postsAPI.getPosts({ sort, limit: 30 });
      setPosts(response.data);
    } catch (error) {
      console.error('Failed to fetch posts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleVote = () => {
    // Refetch posts to update scores
    fetchPosts();
  };

  if (loading) {
    return <div className="text-center py-8">Loading...</div>;
  }

  return (
    <div style={{ padding: '0 4px' }}>
      <table className="hn-table">
        <tbody>
          <tr>
            <td>
              <table className="hn-table">
                <tbody>
                  {posts.map((post, index) => (
                    <tr key={post.id}>
                      <td style={{ textAlign: 'right', verticalAlign: 'top', paddingRight: '4px' }}>
                        <span className="hn-score">{index + 1}.</span>
                      </td>
                      <td style={{ verticalAlign: 'top' }}>
                        <PostItem post={post} onVote={handleVote} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </td>
          </tr>
          {posts.length === 0 && (
            <tr>
              <td style={{ textAlign: 'center', padding: '20px', color: '#828282' }}>
                No posts yet. <Link href="/submit" style={{ color: '#ff6600' }}>Submit</Link> something!
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}