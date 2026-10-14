(function () {
  'use strict';
  // Live updates are an enhancement; normal page refresh and server-side validation remain available.
  if (!window.MOTOBID_AUCTION_ID || typeof window.io !== 'function') return;
  try {
    const socket = window.io({ transports: ['websocket', 'polling'] });
    socket.on('connect', function () { socket.emit('join_auction', { auction_id: window.MOTOBID_AUCTION_ID }); });
    socket.on('bid_update', function (data) {
      if (Number(data.auction_id) !== Number(window.MOTOBID_AUCTION_ID)) return;
      const price = document.getElementById('current-price');
      const count = document.getElementById('bid-count');
      const amount = document.getElementById('amount');
      if (price) price.textContent = '₹' + Number(data.amount).toLocaleString('en-IN');
      if (count) count.textContent = data.bid_count + ' bids';
      if (amount) { amount.min = data.next_bid; amount.value = data.next_bid; }
      const history = document.getElementById('bid-history');
      if (history) {
        const row = document.createElement('div'); row.className = 'bid-row';
        const avatar = document.createElement('div'); avatar.className = 'bid-avatar'; avatar.textContent = (data.bidder || 'B').slice(0, 1).toUpperCase();
        const person = document.createElement('div'); person.className = 'bid-person';
        const name = document.createElement('strong'); name.textContent = data.bidder || 'Bidder';
        const when = document.createElement('span'); when.textContent = 'Just now'; person.append(name, when);
        const bid = document.createElement('strong'); bid.className = 'bid-amount'; bid.textContent = '₹' + Number(data.amount).toLocaleString('en-IN');
        row.append(avatar, person, bid); history.prepend(row);
        while (history.children.length > 20) history.lastElementChild.remove();
      }
    });
  } catch (error) { console.warn('Live bidding updates unavailable; refresh to see current bids.'); }
})();
