class Task < ActiveRecord::Base
  validates :id, presence: true
  validates :title, presence: true
  validates :status, presence: true

  def self.pending
    where(status: 'Pending')
  end

  def self.completed
    where(status: 'Completed')
  end
end