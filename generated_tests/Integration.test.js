// Integration.test.js

const UserController = require('./UserController');
const UserService = require('./UserService');
const UserRepository = require('./UserRepository');
const Database = require('./Database');

jest.mock('./Database');

describe('Integration Test', () => {
  let userController;
  let userService;
  let userRepository;
  let mockDatabase;

  beforeEach(() => {
    mockDatabase = new Database();
    userRepository = new UserRepository(mockDatabase);
    userService = new UserService(userRepository);
    userController = new UserController(userService);
  });

  test('IT-001: Successful Operation and Data Consistency Across All Components', async () => {
    const userId = 'Predefined user ID';
    const userData = 'Predefined user data';

    mockDatabase.findOne.mockResolvedValue(userData);
    mockDatabase.insert.mockResolvedValue(userData);
    mockDatabase.update.mockResolvedValue(userData);
    mockDatabase.delete.mockResolvedValue(true);

    const getUserResult = await userController.getUser(userId);
    expect(getUserResult).toEqual(userData);

    const createUserResult = await userController.createUser(userData);
    expect(createUserResult).toEqual(userData);

    const updateUserResult = await userController.updateUser(userId, userData);
    expect(updateUserResult).toEqual(userData);

    const deleteUserResult = await userController.deleteUser(userId);
    expect(deleteUserResult).toEqual(true);
  });
});