// UserRepository.test.js

const UserRepository = require('./UserRepository');
const Database = require('./Database');

jest.mock('./Database');

describe('UserRepository', () => {
  let userRepository;
  let mockDatabase;

  beforeEach(() => {
    mockDatabase = new Database();
    userRepository = new UserRepository(mockDatabase);
  });

  test('UT-005: Database Operations for User Entity', async () => {
    const userId = 'Predefined user ID';
    const userData = 'Predefined user data';

    mockDatabase.findOne.mockResolvedValue(userData);
    mockDatabase.insert.mockResolvedValue(true);
    mockDatabase.update.mockResolvedValue(true);
    mockDatabase.delete.mockResolvedValue(true);

    const findResult = await userRepository.findById(userId);
    expect(findResult).toEqual(userData);

    const createResult = await userRepository.create(userData);
    expect(createResult).toEqual(true);

    const updateResult = await userRepository.update(userId, userData);
    expect(updateResult).toEqual(true);

    const deleteResult = await userRepository.delete(userId);
    expect(deleteResult).toEqual(true);
  });
});