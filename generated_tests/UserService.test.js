// UserService.test.js

const UserService = require('./UserService');
const UserRepository = require('./UserRepository');

jest.mock('./UserRepository');

describe('UserService', () => {
  let userService;
  let mockUserRepository;

  beforeEach(() => {
    mockUserRepository = new UserRepository();
    userService = new UserService(mockUserRepository);
  });

  test('UT-004: User Data Validation', async () => {
    const invalidUserData = 'Invalid user data';
    await expect(userService.create(invalidUserData)).rejects.toThrow('Email and password are required');
  });
});